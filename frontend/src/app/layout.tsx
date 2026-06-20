import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Tanmay Patil - Digital Twin",
  description:
    "AI digital twin for Tanmay Patil, AI engineer with backend, cloud, and distributed systems experience.",
  keywords: [
    "Tanmay Patil",
    "AI Engineer",
    "AI Digital Twin",
    "Backend Development",
    "Cloud Engineering",
    "Distributed Systems",
    "Java",
    "Spring Boot",
    "Go",
    "Rust",
    "AWS",
    "Docker",
    "Kubernetes",
  ],
  authors: [{ name: "Tanmay Patil" }],
  creator: "Tanmay Patil",
  icons: {
    icon: "/profile.jpeg",
    shortcut: "/profile.jpeg",
    apple: "/profile.jpeg",
  },
  openGraph: {
    title: "Tanmay Patil - AI Digital Twin",
    description:
      "Interact with Tanmay Patil's AI digital twin, trained on professional experience, projects, and technical expertise.",
    url: "https://digitaltwin.tanmayep.dev",
    siteName: "Tanmay Patil",
    locale: "en_US",
    type: "website",
    images: [
      {
        url: "/profile.jpeg",
        width: 800,
        height: 800,
        alt: "Tanmay Patil",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Tanmay Patil - AI Digital Twin",
    description: "Interact with Tanmay Patil's AI digital twin.",
    images: ["/profile.jpeg"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <script
          src="https://rybbit.tanmayep.dev/api/script.js"
          data-site-id="2"
          defer
        ></script>
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
