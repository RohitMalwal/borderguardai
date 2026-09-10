// Panel with a header (title + optional right slot) and a body.
export default function Card({ title, sub, right, children }) {
  return (
    <section className="card">
      {(title || right) && (
        <header className="card-head">
          <div>
            {title && <h3>{title}</h3>}
            {sub && <div className="sub">{sub}</div>}
          </div>
          {right}
        </header>
      )}
      <div className="card-body">{children}</div>
    </section>
  );
}
