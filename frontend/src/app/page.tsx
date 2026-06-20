import Link from "next/link";
import Twin from "@/components/twin";

export default function Home() {
  return (
    <main className="h-screen overflow-hidden bg-[radial-gradient(circle_at_top,#3c3836_0,#1d2021_42rem)] px-4 py-4 text-foreground">
      <section className="mx-auto flex h-full max-w-5xl flex-col gap-4">
        <div className="mx-auto max-w-3xl space-y-2 text-center">
          <p className="text-sm font-medium uppercase tracking-[0.25em] text-primary">
            Tanmay Patil | AI Engineer
          </p>
          <h1 className="text-4xl font-bold tracking-tight text-[#fbf1c7] sm:text-5xl">
            AI Digital Twin
          </h1>
          <p className="text-muted-foreground">
            Ask my AI twin about my work, projects, and technical experience.
          </p>
        </div>

        <div className="min-h-0 flex-1">
          <Twin />
        </div>

        <footer className="text-center text-xs text-muted-foreground">
          <p>
            © {new Date().getFullYear()}{" "}
            <Link href="https://tanmayep.dev" className="hover:text-primary">
              tanmayep.dev
            </Link>
            {". "}
            All rights reserved.
          </p>
          <div className="mt-2 space-x-4">
            <a href="#" className="hover:text-primary">
              Terms of Service
            </a>
            <a href="#" className="hover:text-primary">
              Privacy
            </a>
          </div>
        </footer>
      </section>
    </main>
  );
}
