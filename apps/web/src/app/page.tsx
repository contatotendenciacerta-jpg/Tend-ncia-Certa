import { FooterCta } from "@/components/landing/FooterCta";
import { Hero } from "@/components/landing/Hero";
import { TiersSection } from "@/components/landing/TiersSection";
import { Footer } from "@/components/layout/Footer";
import { PublicHeader } from "@/components/layout/PublicHeader";

export default function HomePage() {
  return (
    <>
      <PublicHeader />
      <main>
        <Hero />
        <TiersSection />
        <FooterCta />
      </main>
      <Footer />
    </>
  );
}
