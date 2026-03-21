export default function Home() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_#dbeafe,_#f8fafc_45%,_#e2e8f0_100%)] px-6 py-16 text-slate-950">
      <div className="mx-auto flex max-w-5xl flex-col gap-10">
        <section className="space-y-4">
          <p className="inline-flex rounded-full border border-sky-200 bg-white/80 px-3 py-1 text-sm font-medium text-sky-700 shadow-sm">
            PDF Chat Monorepo
          </p>
          <div className="space-y-3">
            <h1 className="max-w-3xl text-5xl font-semibold tracking-tight text-balance">
              Upload a PDF and ask AI questions in one workflow.
            </h1>
            <p className="max-w-2xl text-lg leading-8 text-slate-600">
              This frontend is initialized with Next.js and Tailwind. The backend
              is served separately with FastAPI.
            </p>
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-3xl border border-white/70 bg-white/80 p-8 shadow-xl shadow-slate-200/80 backdrop-blur">
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-semibold">Frontend ready</h2>
                <p className="mt-2 text-slate-600">
                  Add file upload, chat history, and streaming answers here.
                </p>
              </div>

              <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
                <p className="text-sm font-medium text-slate-500">Upload area placeholder</p>
                <p className="mt-2 text-sm text-slate-400">
                  Connect this section to the FastAPI upload endpoint next.
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-slate-950 p-8 text-slate-50 shadow-xl shadow-slate-300/40">
            <h2 className="text-2xl font-semibold">Backend endpoints</h2>
            <div className="mt-6 space-y-4 text-sm">
              <div className="rounded-2xl bg-white/10 p-4">
                <p className="font-mono text-sky-300">GET /</p>
                <p className="mt-2 text-slate-300">Basic API status message.</p>
              </div>
              <div className="rounded-2xl bg-white/10 p-4">
                <p className="font-mono text-sky-300">GET /health</p>
                <p className="mt-2 text-slate-300">Health check endpoint for local verification.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
