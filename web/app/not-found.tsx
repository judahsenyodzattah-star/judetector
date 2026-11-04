import Link from "next/link";

export default function NotFound() {
  return (
    <div className="stack">
      <div className="page-header">
        <h1>That page does not exist</h1>
        <p>The link may be out of date.</p>
      </div>
      <p>
        <Link href="/">Return to Home</Link>
      </p>
    </div>
  );
}
