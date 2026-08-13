import { Public_Sans } from 'next/font/google';
import localFont from 'next/font/local';
import { headers } from 'next/headers';
import { ThemeProvider } from '@/components/app/theme-provider';
import { cn } from '@/lib/shadcn/utils';
import { getAppConfig, getStyles } from '@/lib/utils';
import '@/styles/globals.css';

const publicSans = Public_Sans({
  variable: '--font-public-sans',
  subsets: ['latin'],
});

const commitMono = localFont({
  display: 'swap',
  variable: '--font-commit-mono',
  src: [
    {
      path: '../fonts/CommitMono-400-Regular.otf',
      weight: '400',
      style: 'normal',
    },
    {
      path: '../fonts/CommitMono-700-Regular.otf',
      weight: '700',
      style: 'normal',
    },
    {
      path: '../fonts/CommitMono-400-Italic.otf',
      weight: '400',
      style: 'italic',
    },
    {
      path: '../fonts/CommitMono-700-Italic.otf',
      weight: '700',
      style: 'italic',
    },
  ],
});

interface RootLayoutProps {
  children: React.ReactNode;
}

export default async function RootLayout({ children }: RootLayoutProps) {
  const hdrs = await headers();
  const appConfig = await getAppConfig(hdrs);
  const styles = getStyles(appConfig);
  const { pageTitle, pageDescription } = appConfig;

  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={cn(
        publicSans.variable,
        commitMono.variable,
        'scroll-smooth font-sans antialiased dark'
      )}
    >
      <head>
        {styles && <style>{styles}</style>}
        <title>{pageTitle}</title>
        <meta name="description" content={pageDescription} />
      </head>
      <body className="overflow-x-hidden relative min-h-svh bg-[#05080E] text-[#ECEFF4]">
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem={false}
          disableTransitionOnChange
        >
          {/* ── Ambient & 3D Background Layer ── */}
          <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden perspective-1000">
            {/* Tech Dot Grid Pattern Overlay */}
            <div className="absolute inset-0 bg-tech-grid opacity-40" />

            {/* Soft Eye-Friendly Ambient Radial Spotlights */}
            <div className="bg-ambient-orb-1 absolute -top-40 left-1/4 h-[550px] w-[550px] rounded-full bg-cyan-500/12 blur-[150px]" />
            <div className="bg-ambient-orb-2 absolute top-1/3 -right-32 h-[500px] w-[500px] rounded-full bg-blue-600/10 blur-[150px]" />
            <div className="bg-ambient-orb-3 absolute -bottom-32 left-1/3 h-[600px] w-[600px] rounded-full bg-emerald-600/8 blur-[160px]" />

            {/* ── 8 High-Visibility 3D Floating Elements ── */}

            {/* 1. Top-Left Floating 3D Glowing Torus Ring */}
            <div className="absolute top-20 left-6 sm:left-10 opacity-70 animate-3d-float-1 transform-style-3d">
              <svg width="140" height="140" viewBox="0 0 140 140" fill="none" className="drop-shadow-[0_0_15px_rgba(6,182,212,0.4)]">
                <defs>
                  <linearGradient id="torusGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.9" />
                    <stop offset="50%" stopColor="#06B6D4" stopOpacity="0.6" />
                    <stop offset="100%" stopColor="#10B981" stopOpacity="0.3" />
                  </linearGradient>
                  <filter id="glow3d1" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="8" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                  </filter>
                </defs>
                <circle cx="70" cy="70" r="50" stroke="url(#torusGrad1)" strokeWidth="18" filter="url(#glow3d1)" />
                <ellipse cx="70" cy="70" rx="35" ry="16" stroke="rgba(255,255,255,0.4)" strokeWidth="2" />
              </svg>
            </div>

            {/* 2. Top-Right Floating 3D Crystal Octahedron Gem */}
            <div className="absolute top-28 right-8 sm:right-12 opacity-65 animate-3d-float-2 transform-style-3d">
              <svg width="160" height="160" viewBox="0 0 160 160" fill="none" className="drop-shadow-[0_0_15px_rgba(56,189,248,0.35)]">
                <defs>
                  <linearGradient id="gemGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.8" />
                    <stop offset="100%" stopColor="#0284C7" stopOpacity="0.25" />
                  </linearGradient>
                  <linearGradient id="gemGrad2" x1="100%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#06B6D4" stopOpacity="0.7" />
                    <stop offset="100%" stopColor="#0B3B2B" stopOpacity="0.2" />
                  </linearGradient>
                </defs>
                <polygon points="80,10 140,65 80,95 20,65" fill="url(#gemGrad1)" stroke="rgba(255,255,255,0.35)" strokeWidth="1.5" />
                <polygon points="20,65 80,95 80,150" fill="url(#gemGrad2)" stroke="rgba(255,255,255,0.25)" strokeWidth="1" />
                <polygon points="80,95 140,65 80,150" fill="url(#gemGrad1)" stroke="rgba(255,255,255,0.25)" strokeWidth="1" />
              </svg>
            </div>

            {/* 3. Middle-Left Floating 3D Helix Wave Prism */}
            <div className="absolute top-1/2 left-4 sm:left-8 opacity-60 animate-3d-float-2 transform-style-3d -translate-y-1/2">
              <svg width="120" height="180" viewBox="0 0 120 180" fill="none" className="drop-shadow-[0_0_15px_rgba(6,182,212,0.3)]">
                <defs>
                  <linearGradient id="helixGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#06B6D4" stopOpacity="0.85" />
                    <stop offset="50%" stopColor="#38BDF8" stopOpacity="0.5" />
                    <stop offset="100%" stopColor="#10B981" stopOpacity="0.2" />
                  </linearGradient>
                </defs>
                <path d="M20 20 Q 100 50, 20 90 T 20 160" stroke="url(#helixGrad)" strokeWidth="8" strokeLinecap="round" fill="none" />
                <path d="M100 20 Q 20 50, 100 90 T 100 160" stroke="url(#helixGrad)" strokeWidth="4" strokeLinecap="round" opacity="0.6" fill="none" />
              </svg>
            </div>

            {/* 4. Middle-Right Floating 3D Rhombus Crystal Matrix */}
            <div className="absolute top-1/2 right-4 sm:right-8 opacity-60 animate-3d-float-3 transform-style-3d -translate-y-1/2">
              <svg width="140" height="140" viewBox="0 0 140 140" fill="none" className="drop-shadow-[0_0_15px_rgba(2,132,199,0.35)]">
                <defs>
                  <linearGradient id="rhombusGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#0284C7" stopOpacity="0.8" />
                    <stop offset="100%" stopColor="#06B6D4" stopOpacity="0.3" />
                  </linearGradient>
                </defs>
                <polygon points="70,10 130,70 70,130 10,70" fill="url(#rhombusGrad)" stroke="rgba(255,255,255,0.35)" strokeWidth="1.5" />
                <polygon points="70,30 110,70 70,110 30,70" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.25)" strokeWidth="1" />
              </svg>
            </div>

            {/* 5. Top-Center Floating 3D Glass Micro-Spheres Cluster */}
            <div className="absolute top-16 left-1/2 -translate-x-1/2 flex gap-4 opacity-75 animate-subtle-float">
              <div className="h-6 w-6 rounded-full bg-gradient-to-br from-cyan-400 to-blue-600 shadow-lg shadow-cyan-500/40 border border-white/40" />
              <div className="h-4 w-4 rounded-full bg-gradient-to-br from-blue-400 to-emerald-600 shadow-md shadow-blue-500/30 border border-white/30 mt-3" />
              <div className="h-8 w-8 rounded-full bg-gradient-to-br from-teal-400 to-cyan-500 shadow-lg shadow-teal-500/40 border border-white/40 -mt-2" />
            </div>

            {/* 6. Bottom-Left Floating 3D Orbital Sphere */}
            <div className="absolute bottom-24 left-8 sm:left-16 opacity-65 animate-3d-float-3 transform-style-3d">
              <svg width="180" height="180" viewBox="0 0 180 180" fill="none" className="drop-shadow-[0_0_15px_rgba(56,189,248,0.35)]">
                <defs>
                  <radialGradient id="sphereGrad" cx="35%" cy="35%" r="65%">
                    <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.9" />
                    <stop offset="40%" stopColor="#0284C7" stopOpacity="0.5" />
                    <stop offset="100%" stopColor="#05080E" stopOpacity="0.1" />
                  </radialGradient>
                </defs>
                <circle cx="90" cy="90" r="45" fill="url(#sphereGrad)" />
                <ellipse cx="90" cy="90" rx="75" ry="25" stroke="#06B6D4" strokeWidth="2.5" strokeDasharray="6 4" opacity="0.75" transform="rotate(-25 90 90)" />
                <ellipse cx="90" cy="90" rx="60" ry="18" stroke="#10B981" strokeWidth="1.5" opacity="0.5" transform="rotate(35 90 90)" />
              </svg>
            </div>

            {/* 7. Bottom-Right Floating 3D Glass Cube */}
            <div className="absolute bottom-20 right-8 sm:right-20 opacity-60 animate-3d-float-1 transform-style-3d">
              <svg width="130" height="130" viewBox="0 0 130 130" fill="none" className="drop-shadow-[0_0_15px_rgba(6,182,212,0.35)]">
                <defs>
                  <linearGradient id="cubeTop" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.75" />
                    <stop offset="100%" stopColor="#06B6D4" stopOpacity="0.3" />
                  </linearGradient>
                  <linearGradient id="cubeLeft" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#0284C7" stopOpacity="0.5" />
                    <stop offset="100%" stopColor="#05080E" stopOpacity="0.2" />
                  </linearGradient>
                  <linearGradient id="cubeRight" x1="100%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#10B981" stopOpacity="0.5" />
                    <stop offset="100%" stopColor="#06B6D4" stopOpacity="0.2" />
                  </linearGradient>
                </defs>
                <polygon points="65,15 115,40 65,65 15,40" fill="url(#cubeTop)" stroke="rgba(255,255,255,0.35)" strokeWidth="1.5" />
                <polygon points="15,40 65,65 65,115 15,90" fill="url(#cubeLeft)" stroke="rgba(255,255,255,0.2)" strokeWidth="1" />
                <polygon points="65,65 115,40 115,90 65,115" fill="url(#cubeRight)" stroke="rgba(255,255,255,0.2)" strokeWidth="1" />
              </svg>
            </div>

            {/* 8. Bottom-Center Floating 3D Glass Pyramid Prism */}
            <div className="absolute bottom-10 left-1/2 -translate-x-1/2 opacity-60 animate-3d-float-2 transform-style-3d">
              <svg width="150" height="120" viewBox="0 0 150 120" fill="none" className="drop-shadow-[0_0_15px_rgba(16,185,129,0.3)]">
                <defs>
                  <linearGradient id="pyrLeft" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#06B6D4" stopOpacity="0.75" />
                    <stop offset="100%" stopColor="#38BDF8" stopOpacity="0.3" />
                  </linearGradient>
                  <linearGradient id="pyrRight" x1="100%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#0B3B2B" stopOpacity="0.7" />
                    <stop offset="100%" stopColor="#10B981" stopOpacity="0.2" />
                  </linearGradient>
                </defs>
                <polygon points="75,10 15,100 75,115" fill="url(#pyrLeft)" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" />
                <polygon points="75,10 75,115 135,100" fill="url(#pyrRight)" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" />
              </svg>
            </div>
          </div>

          {/* ── Top Header Bar — Dark Eye-Friendly Brand Header ── */}
          <header className="fixed top-0 left-0 z-50 w-full">
            <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
              {/* Logo & Brand Name: Nova */}
              <div className="flex items-center gap-2.5">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-500/15 border border-cyan-400/20 backdrop-blur-md">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" className="text-cyan-400">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <span className="text-[#FAF8F5] text-xl font-bold tracking-tight">
                  Nova
                </span>
              </div>

              {/* Single page indicator & Dashboard shortcut */}
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 rounded-full border border-white/10 bg-[#0C1019]/80 px-3.5 py-1 backdrop-blur-md">
                  <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
                  <span className="text-xs font-semibold text-[#8E9BAE] uppercase tracking-wider">
                    AI Companion
                  </span>
                </div>

                <a
                  href="http://localhost:5050"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 rounded-full border border-cyan-500/20 bg-cyan-500/10 hover:bg-cyan-500/20 px-3.5 py-1 text-xs font-semibold text-[#38BDF8] hover:text-[#FAF8F5] transition-all duration-200 backdrop-blur-md shadow-md shadow-cyan-950/20 hover:scale-[1.03]"
                >
                  📋 Escalation Dashboard
                </a>

                <a
                  href="http://localhost:5051"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 hover:bg-emerald-500/20 px-3.5 py-1 text-xs font-semibold text-[#4ADE80] hover:text-[#FAF8F5] transition-all duration-200 backdrop-blur-md shadow-md shadow-emerald-950/20 hover:scale-[1.03]"
                >
                  📊 Call Analytics
                </a>
              </div>
            </nav>
          </header>

          <main className="relative z-10">{children}</main>
        </ThemeProvider>
      </body>
    </html>
  );
}
