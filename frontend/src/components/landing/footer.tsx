import Link from "next/link";

export function Footer() {
  return (
    <footer className="bg-slate-900 text-slate-50 py-16">
      <div className="container mx-auto px-6">
        <div className="grid md:grid-cols-4 gap-12 mb-12">
          {/* Brand */}
          <div className="md:col-span-1">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center overflow-hidden bg-gradient-to-br from-primary to-primary/80">
                <img src="/logos/app-logo.svg" alt="AEIOU AI" className="w-full h-full object-contain p-2" />
              </div>
              <span className="text-xl font-bold">AEIOU AI</span>
            </div>
            <p className="text-slate-400 text-sm leading-relaxed">
              Your AI Business Partner — Chat, manage tasks, analyze documents, and track goals in one intelligent workspace.
            </p>
          </div>

          {/* Product */}
          <div>
            <h4 className="font-semibold mb-4">Product</h4>
            <ul className="space-y-3 text-sm text-slate-400">
              <li>
                <Link href="/features" className="hover:text-slate-50 transition-colors">
                  Features
                </Link>
              </li>
              <li>
                <Link href="/pricing" className="hover:text-slate-50 transition-colors">
                  Pricing
                </Link>
              </li>
            </ul>
          </div>

          {/* Company */}
          <div>
            <h4 className="font-semibold mb-4">Company</h4>
            <ul className="space-y-3 text-sm text-slate-400">
              <li>
                <Link href="/about" className="hover:text-slate-50 transition-colors">
                  About
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h4 className="font-semibold mb-4">Legal</h4>
            <ul className="space-y-3 text-sm text-slate-400">
              <li>
                <Link href="/privacy" className="hover:text-slate-50 transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/terms" className="hover:text-slate-50 transition-colors">
                  Terms of Service
                </Link>
              </li>
              <li>
                <Link href="/contact" className="hover:text-slate-50 transition-colors">
                  Contact
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-white/10 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-slate-400">
            © {new Date().getFullYear()} AEIOU AI. All rights reserved.
          </p>
          <div className="flex gap-6 text-sm text-slate-400">
            <Link href="/privacy" className="hover:text-slate-50 transition-colors">
              Privacy
            </Link>
            <Link href="/terms" className="hover:text-slate-50 transition-colors">
              Terms
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
