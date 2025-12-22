import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import Link from 'next/link';
import { FileCode, Upload, List, Settings } from 'lucide-react';
import '../styles/globals.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'AWS Cost Calculator',
  description: 'Terraform-based AWS infrastructure cost estimation platform',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} font-sans antialiased`}>
        <div className="min-h-screen bg-gray-50">
          {/* Header */}
          <header className="border-b border-gray-200 bg-white">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
              <div className="flex h-16 items-center justify-between">
                <Link href="/" className="flex items-center gap-2">
                  <FileCode className="h-8 w-8 text-blue-600" />
                  <span className="text-xl font-bold text-gray-900">
                    AWS Cost Calculator
                  </span>
                </Link>
                <nav className="flex items-center gap-6">
                  <Link
                    href="/upload"
                    className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-blue-600"
                  >
                    <Upload className="h-4 w-4" />
                    Upload
                  </Link>
                  <Link
                    href="/jobs"
                    className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-blue-600"
                  >
                    <List className="h-4 w-4" />
                    Jobs
                  </Link>
                  <Link
                    href="/settings"
                    className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-blue-600"
                  >
                    <Settings className="h-4 w-4" />
                    Settings
                  </Link>
                </nav>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
            {children}
          </main>

          {/* Footer */}
          <footer className="mt-auto border-t border-gray-200 bg-white">
            <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
              <p className="text-center text-sm text-gray-500">
                AWS Cost Calculator - Production-grade Terraform cost estimation
              </p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
