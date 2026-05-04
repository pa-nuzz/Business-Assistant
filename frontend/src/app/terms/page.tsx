import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Footer } from "@/components/landing/footer";

export default function TermsPage() {
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
            <Link href="/contact" className="text-muted-foreground hover:text-foreground">Contact</Link>
          </nav>
          <div className="flex items-center gap-3">
            <Link href="/login"><Button variant="ghost" size="sm">Sign In</Button></Link>
            <Link href="/register"><Button size="sm">Get Started</Button></Link>
          </div>
        </div>
      </header>

      <section className="py-16">
        <div className="container mx-auto px-6 max-w-3xl">
          <h1 className="text-3xl font-bold text-foreground mb-2">Terms of Service</h1>
          <p className="text-sm text-muted-foreground mb-8">Last updated: {new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}</p>

          <div className="prose prose-neutral dark:prose-invert max-w-none text-muted-foreground leading-relaxed space-y-6">
            <section>
              <h2 className="text-lg font-semibold text-foreground">1. Acceptance</h2>
              <p>By accessing AEIOU AI, you agree to these Terms. If you do not agree, do not use the service.</p>
            </section>
            <section>
              <h2 className="text-lg font-semibold text-foreground">2. Accounts</h2>
              <p>You are responsible for maintaining the confidentiality of your credentials. Notify us immediately of any unauthorized use. You must be at least 13 years old to use AEIOU AI.</p>
            </section>
            <section>
              <h2 className="text-lg font-semibold text-foreground">3. Acceptable Use</h2>
              <p>You may not use AEIOU AI for unlawful purposes, to transmit malware, to harass others, or to upload content you do not have rights to. We reserve the right to suspend accounts violating these terms.</p>
            </section>
            <section>
              <h2 className="text-lg font-semibold text-foreground">4. AI-Generated Content</h2>
              <p>AI-generated outputs are provided as-is. You are responsible for reviewing and validating AI suggestions, especially for legal, medical, or financial decisions. We do not guarantee accuracy of AI responses.</p>
            </section>
            <section>
              <h2 className="text-lg font-semibold text-foreground">5. Subscriptions & Billing</h2>
              <p>Paid subscriptions are billed in advance. You may cancel anytime; access continues until the end of the billing period. Refunds are evaluated on a case-by-case basis.</p>
            </section>
            <section>
              <h2 className="text-lg font-semibold text-foreground">6. Termination</h2>
              <p>Either party may terminate the service relationship at any time. Upon termination, your data may be retained for a limited period as required by law or for backup purposes, then securely deleted.</p>
            </section>
            <section>
              <h2 className="text-lg font-semibold text-foreground">7. Limitation of Liability</h2>
              <p>AEIOU AI is provided without warranties of any kind. Our liability is limited to the amount you paid in the 12 months preceding the claim.</p>
            </section>
            <section>
              <h2 className="text-lg font-semibold text-foreground">8. Changes</h2>
              <p>We may update these Terms. Material changes will be notified via email or in-app notice. Continued use constitutes acceptance.</p>
            </section>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
