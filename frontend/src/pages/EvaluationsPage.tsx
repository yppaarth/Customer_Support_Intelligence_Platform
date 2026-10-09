export function EvaluationsPage() {
  return (
    <section>
      <h1 className="text-2xl font-semibold">Evaluation Runs</h1>
      <div className="mt-4 rounded border border-line bg-panel p-4 text-sm">
        Run the deterministic suite with <code>python -m app.ai.evaluation.runner --dataset ../../evaluation/datasets/synthetic_support_cases.json --output ../../evaluation/reports/latest.json</code>.
        Reports are written from actual checks and are not hardcoded in the UI.
      </div>
    </section>
  );
}
