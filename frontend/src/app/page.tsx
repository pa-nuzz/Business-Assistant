import { Hero } from "@/components/landing/hero";
import { Features } from "@/components/landing/features";
import { CTA } from "@/components/landing/cta";
import { Footer } from "@/components/landing/footer";

export default function Home() {
  return (
    <main>
      <Hero />
      <Features />
      <CTA />
      <Footer />
    </main>
  );
}
