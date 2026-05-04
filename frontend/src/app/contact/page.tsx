import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Footer } from "@/components/landing/footer";
import { Mail, MapPin } from "lucide-react";

export default function ContactPage() {
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
            <Link href="/about" className="text-muted-foreground hover:text-foreground">About</Link>
            <Link href="/contact" className="text-foreground font-medium">Contact</Link>
          </nav>
          <div className="flex items-center gap-3">
            <Link href="/login"><Button variant="ghost" size="sm">Sign In</Button></Link>
            <Link href="/register"><Button size="sm">Get Started</Button></Link>
          </div>
        </div>
      </header>

      <section className="py-20 md:py-28">
        <div className="container mx-auto px-6 max-w-3xl text-center">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground mb-4">
            Get in touch
          </h1>
          <p className="text-lg text-muted-foreground mb-12">
            Questions, feedback, or enterprise inquiries — we read every message.
          </p>

          <div className="grid md:grid-cols-2 gap-8 text-left">
            <div className="p-6 rounded-2xl border border-border bg-card">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Mail className="w-5 h-5 text-primary" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">Email</h3>
              <p className="text-sm text-muted-foreground mb-3">For sales, support, and general inquiries.</p>
              <a href="mailto:hello@aeiouai.com" className="text-primary hover:underline text-sm font-medium">
                hello@aeiouai.com
              </a>
            </div>
            <div className="p-6 rounded-2xl border border-border bg-card">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <MapPin className="w-5 h-5 text-primary" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">Office</h3>
              <p className="text-sm text-muted-foreground mb-3">
                AEIOU AI HQ<br />
                San Francisco, CA<br />
                United States
              </p>
            </div>
          </div>

          <div className="mt-12 p-8 rounded-2xl border border-border bg-card text-left">
            <h3 className="text-lg font-semibold text-foreground mb-2">Need enterprise support?</h3>
            <p className="text-sm text-muted-foreground mb-6">
              For custom deployments, SSO, SLAs, or data residency requirements, reach out directly.
            </p>
            <a href="mailto:enterprise@aeiouai.com">
              <Button variant="outline">Contact Enterprise Team</Button>
            </a>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
