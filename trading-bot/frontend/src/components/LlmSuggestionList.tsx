export function LlmSuggestionList({ title, items }: { title: string; items: string[] }) {
  return (
    <section className="llmList">
      <h3>{title}</h3>
      {items.length ? (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p style={{ color: "var(--text-muted)", fontSize: 12, margin: 0 }}>データなし</p>
      )}
    </section>
  );
}
