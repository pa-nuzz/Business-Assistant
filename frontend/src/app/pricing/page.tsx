import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Footer } from "@/components/landing/footer";
import { Check, Zap } from "lucide-react";

const tiers = [
  {
    name: "Starter",
    price: "$0",
    period: "/mo",
    description: "For individuals exploring AI-powered productivity.",
    features: ["AI chat with Gemini", "3 documents/month", "Basic task board", "Community support"],
    cta: "Get Started Free",
    href: "/register",
    highlight: false,
  },
  {
    name: "Pro",
    price: "$29",
    period: "/mo",
    description: "For professionals who need AI that understands their business.",
    features: ["All AI providers (Gemini, Groq, OpenRouter)", "Unlimited documents", "Advanced task board + Kanban", "Priority support", "Goal tracking", "Real-time collaboration"],
    cta: "Start Pro Trial",
    href: "/register",
    highlight: true,
  },
  {
    name: "Team",
    price: "$99",
    period: "/mo",
    description: "For teams building together with shared AI context.",
    features: ["Everything in Pro", "Team workspaces", "Shared AI memory", "Admin controls & audit logs", "SSO (coming soon)", "Dedicated onboarding"],
    cta: "Contact Sales",
    href: "/contact",
    highlight: false,
  },
];

export default function PricingPage() {
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
            <Link href="/pricing" className="text-foreground font-medium">Pricing</Link>
            <Link href="/about" className="text-muted-foreground hover:text-foreground">About</Link>
            <Link href="/contact" className="text-muted-foreground hover:text-foreground">Contact</Link>
          </nav>
          <div className="flex items-center gap-3">
            <Link href="/login"><Button variant="ghost" size="sm">Sign In</Button></Link>
            <Link href="/register"><Button size="sm">Get Started</Button></Link>
          </div>
        </div>
      </header>

      <section className="py-20 md:py-28">
        <div className="container mx-auto px-6 text-center">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground mb-4">
            Simple, transparent pricing
          </h1>
          <p className="text-lg text-muted-foreground max-w-xl mx-auto mb-14">
            Start free. Upgrade when AI becomes indispensable to your workflow.
          </p>

          <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {tiers.map((tier) => (
              <div
                key={tier.name}
                className={`relative rounded-2xl border p-8 text-left transition-all ${
                  tier.highlight
                    ? "border-primary bg-primary/5 shadow-lg"
                    : "border-border bg-card hover:border-primary/20"
                }`}
              >
                {tier.highlight && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground text-xs font-semibold px-3 py-1 rounded-full">
                    Most Popular
                  </div>
                )}
                <h3 className="text-lg font-semibold text-foreground mb-1">{tier.name}</h3>
                <div className="flex items-baseline gap-1 mb-3">
                  <span className="text-3xl font-bold text-foreground">{tier.price}</span>
                  <span className="text-muted-foreground text-sm">{tier.period}</span>
                </div>
                <p className="text-sm text-muted-foreground mb-6">{tier.description}</p>
                <ul className="space-y-3 mb-8">
                  {tier.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-sm text-foreground">
                      <Check className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                      {f}
                    </li>
                  ))}
                </ul>
                <Link href={tier.href} className="block">
                  <Button variant={tier.highlight ? "default" : "outline"} className="w-full">
                    {tier.cta}
                  </Button>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
