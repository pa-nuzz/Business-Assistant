import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Footer } from "@/components/landing/footer";

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-sm">A</span>
            </div>
            <span className="font-semibold text-foreground">AEIOU AI</span>
          </Link>
          <nav className="hidden md:flex items-center gap-6 text-sm">
            <Link href="/features" className="text-muted-foreground hover:text-foreground">Features</Link>
            <Link href="/pricing" className="text-muted-foreground hover:text-foreground">Pricing</Link>
            <Link href="/about" className="text-foreground font-medium">About</Link>
            <Link href="/contact" className="text-muted-foreground hover:text-foreground">Contact</Link>
          </nav>
          <div className="flex items-center gap-3">
            <Link href="/login"><Button variant="ghost" size="sm">Sign In</Button></Link>
            <Link href="/register"><Button size="sm">Get Started</Button></Link>
          </div>
        </div>
      </header>

      <section className="py-20 md:py-28">
        <div className="container mx-auto px-6 max-w-3xl">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground mb-8">
            We believe AI should <span className="text-primary">work for you</span>
          </h1>
          <div className="prose prose-neutral dark:prose-invert max-w-none text-muted-foreground leading-relaxed space-y-6">
            <p className="text-lg">
              AEIOU AI was built on a simple idea: the best business assistant does not just answer questions — it understands your goals, manages your tasks, and helps your team move faster.
            </p>
            <p>
              Most AI tools force you to choose between a chatbot, a document analyzer, or a task manager. We combined all three into one workspace that remembers everything, so you never have to repeat yourself.
            </p>
            <p>
              Our architecture is designed for teams that take security seriously. We use memory-only access tokens, httpOnly refresh cookies, and comprehensive audit logging — because your data deserves enterprise-grade protection from day one.
            </p>
            <p>
              AEIOU AI is actively developed by a small team obsessed with craft. Every interaction, every animation, every API response is measured against one standard: does this save the user time?
            </p>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
