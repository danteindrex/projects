'use client'

import Link from 'next/link'
import Image from 'next/image'
import { PlayIcon, ArrowRightIcon } from '@heroicons/react/24/solid'
import { useEffect } from 'react'

export default function HomePage() {
  const integrations = [
    { name: 'Slack', logo: '/integration-logos/slack.svg' },
    { name: 'Asana', logo: '/integration-logos/asana.svg' },
    { name: 'Jira', logo: '/integration-logos/jira.svg' },
    { name: 'GitHub', logo: '/integration-logos/github.svg' },
    { name: 'Salesforce', logo: '/integration-logos/salesforce.svg' },
    { name: 'Zendesk', logo: '/integration-logos/zendesk.svg' },
    { name: 'Trello', logo: '/integration-logos/trello.svg' },
  ]

  useEffect(() => {
    // Trigger heading animations on load
    const headingLines = document.querySelectorAll('.heading-line')
    headingLines.forEach((line) => {
      line.classList.add('animate')
    })
  }, [])

  return (
    <div className="min-h-screen bg-black text-white overflow-hidden">
      {/* Video Background - Full Coverage */}
      <div className="fixed inset-0 w-full h-full z-0">
        <video
          className="absolute inset-0 w-full h-full object-cover"
          autoPlay
          loop
          muted
          playsInline
          aria-hidden="true"
        >
          <source src="/background-video.mp4" type="video/mp4" />
        </video>
        
        {/* Video Overlay */}
        <div className="absolute inset-0 bg-black/75 z-10" aria-hidden="true"></div>
      </div>

      {/* Hero Section */}
      <header className="relative z-20 min-h-screen">
        {/* Navigation - Scale360 Style */}
        <nav className="relative z-20 flex items-center justify-between px-6 py-4 lg:px-12 bg-white/10 backdrop-blur-sm border-b border-white/10" aria-label="Main navigation">
          <div className="flex items-center">
            <Link href="/" className="font-bold text-white hover:text-[#27cbb9] transition-colors" style={{fontSize: 'var(--font-h5)', fontFamily: 'Figtree, Helvetica, Arial, sans-serif'}}>
              Business<span className="text-[#27cbb9]">Hub</span>
              <span className="sr-only">- Home</span>
            </Link>
          </div>
          
          {/* Navigation Menu - Desktop */}
          <div className="hidden md:flex items-center space-x-2">
            <Link href="/dashboard" className="nav-item text-white hover:text-[#27cbb9]" style={{fontSize: 'var(--font-small)', fontFamily: 'Figtree, Helvetica, Arial, sans-serif'}}>
              Dashboard
            </Link>
            <Link href="/integrations" className="nav-item text-white hover:text-[#27cbb9]" style={{fontSize: 'var(--font-small)', fontFamily: 'Figtree, Helvetica, Arial, sans-serif'}}>
              Integrations
            </Link>
            <Link href="/analytics" className="nav-item text-white hover:text-[#27cbb9]" style={{fontSize: 'var(--font-small)', fontFamily: 'Figtree, Helvetica, Arial, sans-serif'}}>
              Analytics
            </Link>
            <Link href="/about" className="nav-item text-white hover:text-[#27cbb9]" style={{fontSize: 'var(--font-small)', fontFamily: 'Figtree, Helvetica, Arial, sans-serif'}}>
              About Us
            </Link>
            <Link href="/contact" className="nav-item text-white hover:text-[#27cbb9]" style={{fontSize: 'var(--font-small)', fontFamily: 'Figtree, Helvetica, Arial, sans-serif'}}>
              Contact
            </Link>
            
            {/* Scale360 Style Button */}
            <Link
              href="/register"
              className="bg-black text-white hover:bg-black transition-all duration-200 font-semibold"
              style={{
                borderRadius: '9999px',
                padding: 'calc(.667em + 2px) calc(1.333em + 2px)',
                fontSize: '1.125em',
                fontFamily: 'Figtree, Helvetica, Arial, sans-serif',
                boxShadow: '0 0 20px rgba(39, 203, 185, 0.3)'
              }}
              onMouseEnter={(e) => {
                const target = e.target as HTMLElement
                target.style.boxShadow = '0 0 40px rgba(39, 203, 185, 0.6)'
                target.style.transform = 'translateY(-2px)'
              }}
              onMouseLeave={(e) => {
                const target = e.target as HTMLElement
                target.style.boxShadow = '0 0 20px rgba(39, 203, 185, 0.3)'
                target.style.transform = 'translateY(0)'
              }}
            >
              Get Started
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden">
            <button className="text-white hover:text-[#27cbb9] transition-colors">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </nav>

        {/* Hero Content */}
        <section className="relative z-20 mx-auto max-w-7xl px-6 py-24 sm:py-32 lg:px-8 lg:py-40" id="main-content" style={{marginTop: '6cm'}}>
          <div className="mx-auto max-w-4xl text-center">
            <h1 
              className="font-bold tracking-tight text-white mb-8"
              style={{
                fontSize: 'clamp(3.2rem, 7.5vw, calc(var(--font-h1) * 1.3))',
                fontFamily: 'Figtree, Helvetica, Arial, sans-serif',
                fontWeight: '600',
                lineHeight: '1.1'
              }}
            >
              <span className="heading-line block">
                <span className="text-[#27cbb9]" style={{fontSize: '1.3em'}}>AI</span> Powered Business Management
              </span>
            </h1>
            
            <h2 
              className="font-bold tracking-tight text-[#27cbb9] mb-8"
              style={{
                fontSize: 'clamp(2.2rem, 6vw, calc(var(--font-h2) * 1.2))',
                fontFamily: 'Figtree, Helvetica, Arial, sans-serif',
                fontWeight: '600',
                lineHeight: '1.3'
              }}
            >
              <span className="heading-line block">Collaborate. Co-Create. Scale.</span>
            </h2>
            
            <p 
              className="text-reveal text-gray-300 max-w-3xl mx-auto mb-12"
              style={{
                fontSize: 'calc(var(--font-body) * 1.2)',
                fontFamily: 'Figtree, Helvetica, Arial, sans-serif',
                lineHeight: '1.6'
              }}
            >
              Streamline your business operations with AI-powered insights and real-time system integration
            </p>
            
            {/* CTA Buttons - Scale360 Style */}
            <div className="text-reveal-delay-2 flex items-center justify-center gap-x-6 flex-wrap">
              <Link
                href="/register"
                className="group flex items-center gap-x-2 bg-[#27cbb9] text-black hover:bg-[#72dbcc] transition-all duration-200 font-semibold shadow-lg hover:shadow-xl transform hover:scale-105"
                style={{
                  borderRadius: '9999px',
                  padding: 'calc(.8em + 4px) calc(1.8em + 4px)',
                  fontSize: '1.125em',
                  fontFamily: 'var(--site-font)'
                }}
                aria-describedby="trial-description"
              >
                Start Free Trial
                <ArrowRightIcon className="h-5 w-5 group-hover:translate-x-1 transition-transform" aria-hidden="true" />
              </Link>
              <button 
                className="group flex items-center gap-x-3 bg-transparent border-2 border-white/30 text-white hover:border-[#27cbb9] hover:text-[#27cbb9] transition-all duration-200 font-semibold backdrop-blur-sm"
                style={{
                  borderRadius: '9999px',
                  padding: 'calc(.8em + 2px) calc(1.8em + 2px)',
                  fontSize: '1.125em',
                  fontFamily: 'var(--site-font)'
                }}
                aria-label="Watch product demonstration video"
              >
                <PlayIcon className="h-6 w-6" aria-hidden="true" />
                Watch Demo
              </button>
            </div>
            <p id="trial-description" className="sr-only">
              Start your free trial to explore all features of BusinessHub with no commitment required.
            </p>
          </div>
        </section>
      </header>

      {/* Integration Carousel Section */}
      <section className="relative z-20 py-24 bg-neutral-900/95 backdrop-blur-sm" aria-labelledby="integrations-heading">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <h2 
              id="integrations-heading" 
              className="font-bold tracking-tight text-white mb-4"
              style={{
                fontSize: 'var(--font-h3)',
                fontFamily: 'var(--site-font)',
                fontWeight: 'var(--font-bold)'
              }}
            >
              Integrate with your favorite tools
            </h2>
            <p 
              className="text-gray-300"
              style={{
                fontSize: 'var(--font-body)',
                fontFamily: 'var(--site-font)',
                lineHeight: '1.6'
              }}
            >
              Connect seamlessly with the platforms your team already uses
            </p>
          </div>
          
          {/* Continuous Scrolling Integration Carousel */}
          <div className="mt-16 overflow-hidden">
            <div className="flex animate-scroll-right space-x-16">
              {[...integrations, ...integrations].map((integration, index) => (
                <Image
                  key={`${integration.name}-${index}`}
                  src={integration.logo}
                  alt={integration.name}
                  width={80}
                  height={80}
                  className="flex-shrink-0 w-20 h-20 object-contain filter brightness-110 hover:brightness-125 transition-all duration-300"
                />
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* How to Get Started Section */}
      <section className="relative z-20 py-24 bg-black/95 backdrop-blur-sm" aria-labelledby="getting-started-heading">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <h2 
              id="getting-started-heading" 
              className="font-bold tracking-tight text-white mb-4"
              style={{
                fontSize: 'var(--font-h3)',
                fontFamily: 'var(--site-font)',
                fontWeight: 'var(--font-bold)'
              }}
            >
              How to get started
            </h2>
            <p 
              className="text-gray-300"
              style={{
                fontSize: 'var(--font-body)',
                fontFamily: 'var(--site-font)',
                lineHeight: '1.6'
              }}
            >
              Get up and running with BusinessHub in just three simple steps
            </p>
          </div>
          
          <div className="mt-16 grid grid-cols-1 gap-8 lg:grid-cols-3">
            <article className="container-hover bg-neutral-900 rounded-2xl p-8 border border-gray-800 hover:border-[#27cbb9] relative">
              <div className="absolute inset-0 bg-gradient-to-br from-[#27cbb9]/10 to-transparent rounded-2xl opacity-0 hover:opacity-100" aria-hidden="true"></div>
              <div className="relative">
                <div className="w-12 h-12 bg-[#27cbb9] rounded-full flex items-center justify-center text-black font-bold text-xl mb-6" aria-hidden="true">1</div>
                <h3 
                  className="text-white mb-3"
                  style={{
                    fontSize: 'var(--font-h6)',
                    fontFamily: 'var(--site-font)',
                    fontWeight: 'var(--font-bold)'
                  }}
                >
                  Sign Up & Connect
                </h3>
                <p 
                  className="text-gray-300"
                  style={{
                    fontSize: 'var(--font-small)',
                    fontFamily: 'var(--site-font)',
                    lineHeight: '1.6'
                  }}
                >
                  Create your free account and connect your first business application. 
                  Our setup wizard guides you through the process in minutes.
                </p>
              </div>
            </article>
            
            <article className="container-hover bg-neutral-900 rounded-2xl p-8 border border-gray-800 hover:border-[#27cbb9] relative">
              <div className="absolute inset-0 bg-gradient-to-br from-[#27cbb9]/10 to-transparent rounded-2xl opacity-0 hover:opacity-100" aria-hidden="true"></div>
              <div className="relative">
                <div className="w-12 h-12 bg-[#27cbb9] rounded-full flex items-center justify-center text-black font-bold text-xl mb-6" aria-hidden="true">2</div>
                <h3 
                  className="text-white mb-3"
                  style={{
                    fontSize: 'var(--font-h6)',
                    fontFamily: 'var(--site-font)',
                    fontWeight: 'var(--font-bold)'
                  }}
                >
                  Configure & Customize
                </h3>
                <p 
                  className="text-gray-300"
                  style={{
                    fontSize: 'var(--font-small)',
                    fontFamily: 'var(--site-font)',
                    lineHeight: '1.6'
                  }}
                >
                  Set up your integrations, customize dashboards, and configure alerts. 
                  Tailor the platform to match your team&apos;s specific workflow needs.
                </p>
              </div>
            </article>
            
            <article className="container-hover bg-neutral-900 rounded-2xl p-8 border border-gray-800 hover:border-[#27cbb9] relative">
              <div className="absolute inset-0 bg-gradient-to-br from-[#27cbb9]/10 to-transparent rounded-2xl opacity-0 hover:opacity-100" aria-hidden="true"></div>
              <div className="relative">
                <div className="w-12 h-12 bg-[#27cbb9] rounded-full flex items-center justify-center text-black font-bold text-xl mb-6" aria-hidden="true">3</div>
                <h3 
                  className="text-white mb-3"
                  style={{
                    fontSize: 'var(--font-h6)',
                    fontFamily: 'var(--site-font)',
                    fontWeight: 'var(--font-bold)'
                  }}
                >
                  Monitor & Optimize
                </h3>
                <p 
                  className="text-gray-300"
                  style={{
                    fontSize: 'var(--font-small)',
                    fontFamily: 'var(--site-font)',
                    lineHeight: '1.6'
                  }}
                >
                  Start monitoring your systems in real-time. Use AI-powered insights 
                  to identify bottlenecks and optimize your business processes.
                </p>
              </div>
            </article>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative z-20 py-24 bg-gradient-to-r from-[#27cbb9] to-[#72dbcc]" aria-labelledby="cta-heading">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <h2 
              id="cta-heading" 
              className="font-bold tracking-tight text-black mb-4"
              style={{
                fontSize: 'var(--font-h3)',
                fontFamily: 'var(--site-font)',
                fontWeight: 'var(--font-bold)'
              }}
            >
              Ready to transform your business operations?
            </h2>
            <p 
              className="text-black/80"
              style={{
                fontSize: 'var(--font-body)',
                fontFamily: 'var(--site-font)',
                lineHeight: '1.6'
              }}
            >
              Join thousands of companies who trust BusinessHub to manage their systems
            </p>
            <div className="mt-8">
              <Link
                href="/register"
                className="inline-flex items-center gap-x-2 bg-black text-white hover:bg-neutral-800 transition-all duration-200 font-semibold shadow-lg hover:shadow-xl transform hover:scale-105"
                style={{
                  borderRadius: '9999px',
                  padding: 'calc(.8em + 4px) calc(1.8em + 4px)',
                  fontSize: '1.125em',
                  fontFamily: 'var(--site-font)'
                }}
              >
                Get Started Today
                <ArrowRightIcon className="h-5 w-5" aria-hidden="true" />
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
