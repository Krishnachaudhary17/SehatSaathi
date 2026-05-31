export default function Page() {
  return (
    <main style={{ width: "100%", height: "100vh", overflow: "hidden" }}>
      <iframe
        src="/physio-tracker.html"
        style={{ width: "100%", height: "100%", border: "none" }}
        title="PhysioAI Exercise Coach"
      />
    </main>
  );
}
