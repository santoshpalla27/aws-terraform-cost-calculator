import Link from 'next/link';
import { Upload, List, TrendingUp, Zap } from 'lucide-react';

export default function Home() {
  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <div className="text-center">
        <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
          AWS Cost Estimation
        </h1>
        <p className="mt-6 text-lg leading-8 text-gray-600 max-w-2xl mx-auto">
          Upload your Terraform files and get accurate cost estimates for your AWS
          infrastructure before deployment. Make informed decisions with confidence.
        </p>
        <div className="mt-10 flex items-center justify-center gap-4">
          <Link
            href="/upload"
            className="rounded-md bg-blue-600 px-6 py-3 text-base font-semibold text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Get Started
          </Link>
          <Link
            href="/jobs"
            className="rounded-md border border-gray-300 bg-white px-6 py-3 text-base font-semibold text-gray-900 shadow-sm hover:bg-gray-50"
          >
            View Jobs
          </Link>
        </div>
      </div>

      {/* Features */}
      <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
        <FeatureCard
          icon={<Upload className="h-8 w-8 text-blue-600" />}
          title="Easy Upload"
          description="Simply upload your Terraform files or ZIP archives to get started"
        />
        <FeatureCard
          icon={<TrendingUp className="h-8 w-8 text-blue-600" />}
          title="Accurate Estimates"
          description="Get detailed cost breakdowns by service and resource with confidence scores"
        />
        <FeatureCard
          icon={<Zap className="h-8 w-8 text-blue-600" />}
          title="Real-time Updates"
          description="Track job progress in real-time with live status updates"
        />
      </div>

      {/* How It Works */}
      <div className="rounded-lg border border-gray-200 bg-white p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">How It Works</h2>
        <div className="space-y-4">
          <Step
            number={1}
            title="Upload Terraform Files"
            description="Upload your .tf files or a ZIP archive containing your infrastructure code"
          />
          <Step
            number={2}
            title="Select Usage Profile"
            description="Choose a usage profile (dev/prod) or customize assumptions for your workload"
          />
          <Step
            number={3}
            title="Get Cost Estimate"
            description="Receive detailed cost breakdowns, warnings, and confidence scores for each resource"
          />
        </div>
      </div>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6">
      <div className="mb-4">{icon}</div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
    </div>
  );
}

function Step({
  number,
  title,
  description,
}: {
  number: number;
  title: string;
  description: string;
}) {
  return (
    <div className="flex gap-4">
      <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-semibold text-white">
        {number}
      </div>
      <div>
        <h4 className="font-semibold text-gray-900">{title}</h4>
        <p className="text-sm text-gray-600">{description}</p>
      </div>
    </div>
  );
}
