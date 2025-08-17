import Link from 'next/link'
import { ArrowRightIcon } from '@heroicons/react/24/outline'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-teal-50">
      <div className="relative isolate px-6 pt-14 lg:px-8">
        <div className="mx-auto max-w-2xl py-32 sm:py-48 lg:py-56">
          <div className="text-center">
            <h1 className="text-4xl font-bold tracking-tight text-neutral-900 sm:text-6xl">
              Business Systems
              <span className="text-primary-600"> Integration</span>
            </h1>
            <p className="mt-6 text-lg leading-8 text-neutral-600">
              Connect, monitor, and manage all your business systems through a single AI-powered platform. 
              Real-time insights, intelligent automation, and seamless integration.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Link
                href="/dashboard"
                className="rounded-md bg-primary-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-primary-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
              >
                Get started
                <ArrowRightIcon className="ml-2 -mr-1 h-4 w-4 inline" />
              </Link>
              <Link
                href="/integrations"
                className="text-sm font-semibold leading-6 text-neutral-900 hover:text-primary-600"
              >
                View Integrations <span aria-hidden="true">→</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
