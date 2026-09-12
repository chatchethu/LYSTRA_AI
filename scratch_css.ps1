$cssPath = "frontend\app\globals.css"
$newCss = @"
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    /* 
      Phase 2, 3, 27: Premium, Calm, Minimal Design Tokens 
      Light Mode Defaults 
    */
    --bg-base: #FFFFFF;
    --bg-surface: #F9FAFB;
    --bg-elevated: #FFFFFF;
    
    --text-primary: #111827;
    --text-secondary: #6B7280;
    --text-tertiary: #9CA3AF;
    
    --border-subtle: #F3F4F6;
    --border-strong: #E5E7EB;
    
    --accent-primary: #0F172A;
    --accent-hover: #1E293B;
    
    --radius-sm: 6px;
    --radius-md: 10px;
    --radius-lg: 16px;
    --radius-full: 9999px;
    
    /* Phase 33: Animation System */
    --motion-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
    --motion-standard: 250ms cubic-bezier(0.4, 0, 0.2, 1);
    --motion-emphasis: 400ms cubic-bezier(0.4, 0, 0.2, 1);
    
    --shadow-subtle: 0 1px 2px rgba(0, 0, 0, 0.05);
    --shadow-elevated: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
  }

  .dark {
    --bg-base: #09090B;
    --bg-surface: #121214;
    --bg-elevated: #18181B;
    
    --text-primary: #FAFAFA;
    --text-secondary: #A1A1AA;
    --text-tertiary: #71717A;
    
    --border-subtle: #27272A;
    --border-strong: #3F3F46;
    
    --accent-primary: #FAFAFA;
    --accent-hover: #E4E4E7;
    
    --shadow-subtle: 0 1px 2px rgba(0, 0, 0, 0.5);
    --shadow-elevated: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
  }

  body {
    @apply bg-[var(--bg-base)] text-[var(--text-primary)] antialiased;
    font-family: 'Inter', sans-serif;
  }
}

/* Phase 28: Typography Hierarchy */
@layer utilities {
  .text-h1 { @apply text-2xl font-semibold tracking-tight; }
  .text-h2 { @apply text-lg font-medium tracking-tight; }
  .text-body { @apply text-[15px] leading-relaxed; }
  .text-meta { @apply text-[13px] text-[var(--text-secondary)]; }
  
  .transition-fast { transition: all var(--motion-fast); }
  .transition-standard { transition: all var(--motion-standard); }
}

/* Scrollbar Polish */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: var(--radius-full); }
::-webkit-scrollbar-thumb:hover { background: var(--text-tertiary); }

"@
Set-Content -Path $cssPath -Value $newCss
