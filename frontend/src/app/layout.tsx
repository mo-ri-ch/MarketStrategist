import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'MarketStrategist - Competitor Intelligence AI Assistant',
  description: 'AI-powered SaaS platform to monitor competitors, discover opportunities, and receive CEO-level strategic recommendations.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body className="antialiased min-h-screen bg-dark-500 text-foreground font-sans">
        {children}
      </body>
    </html>
  )
}
