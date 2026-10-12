from __future__ import annotations

"""Module 4: RAGAS Evaluation — 4 metrics + failure analysis."""

import copy
import os, sys, json
from math import isfinite
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (EVALUATOR_EMBEDDING_MODEL, EVALUATOR_LLM_MODEL,
                    GOOGLE_API_KEY, OPENAI_API_KEY, OPENAI_BASE_URL, TEST_SET_PATH)


@dataclass
class EvalResult:
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float


def load_test_set(path: str = TEST_SET_PATH) -> list[dict]:
    """Load test set from JSON. (Đã implement sẵn)"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _safe_float(value, default=0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"RAGAS returned a non-numeric metric: {value!r}") from None
    if not isfinite(parsed) or not 0 <= parsed <= 1:
        raise ValueError(f"RAGAS metric must be finite and within [0, 1]: {value!r}")
    return parsed


class GoogleGenAIEmbeddings:
    """LangChain-compatible adapter for Gemini's native embedding API."""

    def __init__(self, client):
        self.client = client

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self.client.models.embed_content(
            model=EVALUATOR_EMBEDDING_MODEL,
            contents=texts,
        )
        embeddings = getattr(response, "embeddings", None)
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise ValueError("Gemini embeddings response did not match the requested texts.")
        vectors = []
        for embedding in embeddings:
            values = getattr(embedding, "values", None)
            if not isinstance(values, list) or not values:
                raise ValueError("Gemini returned an empty or invalid embedding vector.")
            vector = [float(value) for value in values]
            if any(not isfinite(value) for value in vector):
                raise ValueError("Gemini embedding vector contains a non-finite value.")
            vectors.append(vector)
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


def _heuristic_eval(questions: list[str], answers: list[str],
                   contexts: list[list[str]], ground_truths: list[str]) -> dict:
    """Fallback heuristic evaluation used when RAGAS / API access is unavailable."""
    per_question: list[EvalResult] = []
    metrics = {"faithfulness": [], "answer_relevancy": [], "context_precision": [], "context_recall": []}

    for question, answer, context_list, ground_truth in zip(questions, answers, contexts, ground_truths):
        q_tokens = set((question or "").lower().replace("?", "").split())
        gt_tokens = set((ground_truth or "").lower().replace("?", "").split())
        ans_tokens = set((answer or "").lower().replace("?", "").split())

        overlap = len(q_tokens & gt_tokens) / max(len(gt_tokens), 1)
        answer_overlap = len(ans_tokens & gt_tokens) / max(len(gt_tokens), 1)
        context_overlap = len(set((" ".join(context_list)).lower().split()) & gt_tokens) / max(len(gt_tokens), 1)

        faithfulness = min(1.0, max(0.0, 0.35 + 0.65 * answer_overlap))
        answer_relevancy = min(1.0, max(0.0, 0.4 + 0.6 * overlap))
        context_precision = min(1.0, max(0.0, 0.5 + 0.5 * (1.0 if context_list else 0.0)))
        context_recall = min(1.0, max(0.0, 0.3 + 0.7 * context_overlap))

        perf = EvalResult(
            question=question,
            answer=answer,
            contexts=context_list,
            ground_truth=ground_truth,
            faithfulness=faithfulness,
            answer_relevancy=answer_relevancy,
            context_precision=context_precision,
            context_recall=context_recall,
        )
        per_question.append(perf)

        for key, val in {
            "faithfulness": faithfulness,
            "answer_relevancy": answer_relevancy,
            "context_precision": context_precision,
            "context_recall": context_recall,
        }.items():
            metrics[key].append(val)

    aggregate = {
        "faithfulness": sum(metrics["faithfulness"]) / max(len(metrics["faithfulness"]), 1),
        "answer_relevancy": sum(metrics["answer_relevancy"]) / max(len(metrics["answer_relevancy"]), 1),
        "context_precision": sum(metrics["context_precision"]) / max(len(metrics["context_precision"]), 1),
        "context_recall": sum(metrics["context_recall"]) / max(len(metrics["context_recall"]), 1),
        "per_question": per_question,
    }
    return aggregate


def evaluate_ragas(questions: list[str], answers: list[str],
                   contexts: list[list[str]], ground_truths: list[str]) -> dict:
    """Run genuine RAGAS metrics with explicitly configured Gemini models.

    Provider, dependency, and per-row metric errors are raised; none are replaced
    by synthetic heuristic scores in a submission run.
    """
    if not GOOGLE_API_KEY:
        raise RuntimeError("Set GOOGLE_API_KEY to run genuine Gemini-backed RAGAS evaluation.")
    if not (len(questions) == len(answers) == len(contexts) == len(ground_truths)):
        raise ValueError("Questions, answers, contexts, and references must have equal lengths.")

    from datasets import Dataset
    from google import genai
    from langchain_openai import ChatOpenAI
    from ragas import evaluate
    from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness
    from ragas.run_config import RunConfig

    if OPENAI_BASE_URL != "https://generativelanguage.googleapis.com/v1beta/openai":
        raise ValueError("RAGAS evaluator requires the configured Google AI Studio OpenAI-compatible endpoint.")
    if not OPENAI_API_KEY:
        raise RuntimeError("No API key is configured for the Gemini-compatible chat model.")

    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    })
    llm = ChatOpenAI(
        model=EVALUATOR_LLM_MODEL,
        temperature=0,
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
        max_retries=8,
        timeout=120,
    )
    embedding_client = genai.Client(api_key=GOOGLE_API_KEY)
    embeddings = GoogleGenAIEmbeddings(embedding_client)
    metrics = [copy.deepcopy(metric) for metric in (
        faithfulness, answer_relevancy, context_precision, context_recall
    )]
    # Gemini's OpenAI-compatible endpoint does not support multiple candidates
    # in one request; use one generated question per answer-relevancy score.
    metrics[1].strictness = 1
    result = evaluate(
        dataset,
        metrics=metrics,
        llm=llm,
        embeddings=embeddings,
        run_config=RunConfig(timeout=600, max_retries=8, max_wait=60, max_workers=2),
        raise_exceptions=True,
    )
    df = result.to_pandas()
    if len(df) != len(questions):
        raise ValueError(f"RAGAS returned {len(df)} rows for {len(questions)} inputs.")

    per_question = []
    for _, row in df.iterrows():
        per_question.append(EvalResult(
            question=str(row["question"]),
            answer=str(row["answer"]),
            contexts=list(row["contexts"]),
            ground_truth=str(row["ground_truth"]),
            faithfulness=_safe_float(row["faithfulness"]),
            answer_relevancy=_safe_float(row["answer_relevancy"]),
            context_precision=_safe_float(row["context_precision"]),
            context_recall=_safe_float(row["context_recall"]),
        ))

    aggregate = {
        metric: sum(getattr(item, metric) for item in per_question) / len(per_question)
        for metric in ("faithfulness", "answer_relevancy", "context_precision", "context_recall")
    }
    aggregate["per_question"] = per_question
    aggregate["metadata"] = {
        "evaluator_models": sorted({EVALUATOR_LLM_MODEL, EVALUATOR_EMBEDDING_MODEL}),
        "evaluator_backend": "ragas",
    }
    return aggregate


def failure_analysis(eval_results: list[EvalResult], bottom_n: int = 10) -> list[dict]:
    """Analyze worst-performing questions using a simple diagnostic tree."""
    diagnostic_tree = {
        "faithfulness": ("LLM hallucinating", "Tighten the prompt, shorten context, and reduce temperature."),
        "context_recall": ("Missing relevant chunks", "Improve chunking, add BM25 coverage, or widen retrieval depth."),
        "context_precision": ("Too many irrelevant chunks", "Add reranking, metadata filtering, or stronger query expansion."),
        "answer_relevancy": ("Answer does not match the question", "Refine prompt instructions and make the answer more grounded in the retrieved context."),
    }

    ranked = []
    for item in eval_results:
        scores = {
            "faithfulness": float(item.faithfulness),
            "answer_relevancy": float(item.answer_relevancy),
            "context_precision": float(item.context_precision),
            "context_recall": float(item.context_recall),
        }
        avg_score = sum(scores.values()) / max(len(scores), 1)
        worst_metric = min(scores, key=scores.get)
        diagnosis, fix = diagnostic_tree.get(worst_metric, ("Unclear failure", "Review retrieval and answer prompt logic."))
        ranked.append({
            "question": item.question,
            "worst_metric": worst_metric,
            "score": scores[worst_metric],
            "avg_score": avg_score,
            "diagnosis": diagnosis,
            "suggested_fix": fix,
        })

    ranked.sort(key=lambda x: (x["avg_score"], x["score"]))
    return ranked[:max(0, int(bottom_n))]


def save_report(results: dict, failures: list[dict], path: str = "reports/ragas_report.json"):
    """Save evaluation report to JSON. (Đã implement sẵn)"""
    parent_dir = os.path.dirname(path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    report = {
        "aggregate": {k: v for k, v in results.items() if k != "per_question"},
        "num_questions": len(results.get("per_question", [])),
        "failures": failures,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Report saved to {path}")


if __name__ == "__main__":
    test_set = load_test_set()
    print(f"Loaded {len(test_set)} test questions")
    print("Run pipeline.py first to generate answers, then call evaluate_ragas().")
