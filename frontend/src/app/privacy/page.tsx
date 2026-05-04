import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Footer } from "@/components/landing/footer";

export default function PrivacyPage() {
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
          <h1 className="text-3xl font-bold text-foreground mb-2">Privacy Policy</h1>
          <p className="text-sm text-muted-foreground mb-8">Last updated: {new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}</p>

          <div className="prose prose-neutral dark:prose-invert max-w-none text-muted-foreground leading-relaxed space-y-6">
            <section>
              <h2 className="text-lg font-semibold text-foreground">1. Information We Collect</h2>
              <p>We collect account information (name, email), documents you upload for AI analysis, conversation content, and usage analytics to improve the product. We do not sell your data.</p>
            </section>
            <section>
              <h2 className="text-lg font-semibold text-foreground">2. How We Use Data</h2>
              <p>Your data is used to provide AI services, manage tasks and goals, enable team collaboration, and maintain security through audit logging. AI providers may process conversation content under strict confidentiality agreements.</p>
            </section>
            <section>
              <h2 className="text-lg font-semibold text-foreground">3. Security</h2>
              <p>We use JWT authentication with httpOnly cookies, TLS encryption in transit, encrypted storage at rest, and role-based access controls. Memory-only access tokens ensure browser compromise does not expose long-lived credentials.</p>
            </section>
            <section>
              <h2 className="text-lg font-semibold text-foreground">4. Data Retention</h2>
              <p>Account data is retained while your account is active. Documents and conversations can be deleted by workspace admins. Deleted data is purged within 30 days.</p>
            </section>
            <section>
              <h2 className="text-lg font-semibold text-foreground">5. Your Rights</h2>
              <p>You can access, export, or delete your data at any time through account settings. Contact us at hello@aeiouai.com for data portability requests.</p>
            </section>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
