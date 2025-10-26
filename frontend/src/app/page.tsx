import Twin from "@/components/twin";
import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-gray-100">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl font-bold text-center text-gray-800 mb-2">
            Tanmay Ekanath Patil
          </h1>
          <p className="text-center text-gray-600 mb-8">
            Software Developer | Backend Engineer | Cloud Architect
          </p>
          <p className="text-center text-gray-500 mb-8 max-w-2xl mx-auto">
            Interact with my AI digital twin - trained on my professional experience,
            projects, and technical expertise in backend development, distributed systems,
            and cloud engineering.
          </p>

          <div className="h-[600px]">
            <Twin />
          </div>

          <footer className="mt-8 text-center text-xs text-gray-500">
            <p>
              © {new Date().getFullYear()}{" "}
              <span className="hover:text-gray-700">
                <Link href={"https://tanmayep.dev"}>tanmayep.dev</Link>
              </span>
              {". "}
              All rights reserved.
            </p>
            <div className="mt-2 space-x-4">
              <a href="#" className="hover:text-gray-700">
                Terms of Service
              </a>
              <a href="#" className="hover:text-gray-700">
                Privacy
              </a>
            </div>
          </footer>
        </div>
      </div>
    </main>
  );
}
