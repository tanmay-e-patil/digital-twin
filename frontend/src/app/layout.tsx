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
    "Software Developer with 5 years of experience in backend engineering, cloud-based applications, and distributed systems. Specializing in Java, Spring Boot, Go, Rust, AWS, Docker, and Kubernetes.",
  keywords: [
    "Software Developer",
    "Backend Development",
    "Cloud Engineering",
    "DevOps",
    "Distributed Systems",
    "API Design",
    "Java",
    "Spring Boot",
    "Go",
    "Rust",
    "AWS",
    "Docker",
    "Kubernetes",
    "CI/CD",
    "Full-stack Development",
  ],
  authors: [{ name: "Tanmay Ekanath Patil" }],
  creator: "Tanmay Ekanath Patil",
  icons: {
    icon: "/profile.jpeg",
    shortcut: "/profile.jpeg",
    apple: "/profile.jpeg",
  },
  openGraph: {
    title: "Tanmay Ekanath Patil - Software Developer",
    description:
      "Software Developer with 5 years of experience in backend engineering, cloud-based applications, and distributed systems.",
    url: "https://digitaltwin.tanmayep.dev",
    siteName: "Tanmay Ekanath Patil",
    locale: "en_US",
    type: "website",
    images: [
      {
        url: "/profile.jpeg",
        width: 800,
        height: 800,
        alt: "Tanmay Ekanath Patil",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Tanmay Ekanath Patil - Software Developer",
    description:
      "Software Developer with 5 years of experience in backend engineering, cloud-based applications, and distributed systems.",
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
