import React, { useState } from 'react';
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  Clock3,
  Instagram,
  MapPin,
  Menu,
  Scissors,
  X,
} from 'lucide-react';

import BookingFlow from '../components/BookingFlow';
import { studio } from '../config/studio';
import { fmtEUR } from '../utils';

/**
 * Aaron Binions — Customer-facing website
 *
 * Services, availability and prices are loaded from the backend.
 * Booking functionality is handled by the reusable BookingFlow component.
 */
export default function Storefront({ data }) {
  const [booking, setBooking] = useState(false);
  const [selectedService, setSelectedService] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);

  const book = (service = null) => {
    setSelectedService(service);
    setMenuOpen(false);
    setBooking(true);
  };

  const closeMenu = () => setMenuOpen(false);

  return (
    <div className="aaron-site v3-site">

      {/* Development notice */}
      <div className="v3-preview" role="status">
        Website preview — service prices and hours are not yet confirmed
      </div>

      {/* HEADER */}
      <header className="v3-header">
        <div className="v3-container v3-header-inner">

          <a
            className="v3-brand"
            href="#home"
            aria-label="Aaron Binions home"
            onClick={closeMenu}
          >
            <span className="v3-mark">
              AB<span>.</span>
            </span>

            <span className="v3-brand-text">
              Aaron Binions
              <small>BARBER · MONASTEREVIN</small>
            </span>
          </a>

          <nav
            aria-label="Main navigation"
            className={
              menuOpen
                ? 'v3-navigation is-open'
                : 'v3-navigation'
            }
          >
            <a onClick={closeMenu} href="#services">
              Services
            </a>

            <a onClick={closeMenu} href="#about">
              About
            </a>

            <a onClick={closeMenu} href="#reviews">
              Reviews
            </a>

            <a
              onClick={closeMenu}
              href={studio.instagram}
              target="_blank"
              rel="noreferrer"
            >
              Instagram <ArrowUpRight size={13} />
            </a>
          </nav>

          <div className="v3-header-actions">
            <button
              type="button"
              className="v3-button v3-button-light v3-nav-cta"
              onClick={() => book()}
            >
              Book appointment
              <ArrowUpRight size={16} />
            </button>

            <button
              type="button"
              className="v3-menu"
              onClick={() => setMenuOpen(!menuOpen)}
              aria-expanded={menuOpen}
              aria-label="Toggle navigation"
            >
              {menuOpen ? <X size={22} /> : <Menu size={22} />}
            </button>
          </div>

        </div>
      </header>

      <main>

        {/* HERO */}
        <section id="home" className="v3-hero">

          <div
            className="v3-hero-sheen"
            aria-hidden="true"
          />

          <div className="v3-container v3-hero-grid">

            <div className="v3-hero-copy">

              <div className="v3-kicker">
                <span className="v3-kicker-line" />
                INDEPENDENT BARBER · MONASTEREVIN
              </div>

              <h1>
                Aaron
                <br />
                Binions
                <span className="v3-title-dot">.</span>
              </h1>

              <div className="v3-hero-subheading">
                Barbering by appointment.
              </div>

              <p>
                Welcome to my private barber studio in Monasterevin,
                Co. Kildare. You can view my services and book your
                next appointment online.
              </p>

              <div className="v3-hero-buttons">

                <button
                  type="button"
                  className="v3-button v3-button-light"
                  onClick={() => book()}
                >
                  Book an appointment
                  <ArrowUpRight size={17} />
                </button>

                <a
                  className="v3-secondary-link"
                  href="#services"
                >
                  View services
                  <ArrowRight size={17} />
                </a>

              </div>
            </div>

            <div className="v3-hero-side">

              <div className="v3-photo-panel">

                <div className="v3-photo-top">
                  <span>YOUR BARBER</span>
                  <span>01 / 01</span>
                </div>

                <div className="v3-photo-ring">
                  <img
                    src={studio.picture}
                    alt="Aaron Binions, independent barber"
                  />
                </div>

                <div className="v3-photo-bottom">
                  <span>AARON BINIONS</span>
                  <span>MONASTEREVIN, KILDARE</span>
                </div>

              </div>
            </div>

          </div>

          <div className="v3-container v3-hero-facts">

            <span>
              <Check size={15} />
              Independent barber
            </span>

            <span>
              <Check size={15} />
              6+ years' experience
            </span>

            <span>
              <Check size={15} />
              Private studio appointments
            </span>

          </div>

        </section>

        {/* SERVICES */}
        <section
          id="services"
          className="v3-section v3-services"
        >
          <div className="v3-container">

            <div className="v3-section-head">

              <div>
                <div className="v3-overline">
                  SERVICES
                </div>

                <h2>Services &amp; prices</h2>
              </div>

              <p>
                Take a look at my services below. Select the
                treatment you're after to check available appointments.
              </p>

            </div>

            <div className="v3-services-list">

              {data.services.map((service) => (
                <button
                  key={service.id}
                  className="v3-service"
                  type="button"
                  onClick={() => book(service)}
                >

                  <span className="v3-service-icon">
                    <Scissors size={21} />
                  </span>

                  <span className="v3-service-description">
                    <strong>{service.name}</strong>

                    <small>
                      {service.description ||
                        'Select to book an appointment.'}
                    </small>
                  </span>

                  <span className="v3-service-duration">
                    <Clock3 size={15} />
                    {service.duration_min} min
                  </span>

                  <span className="v3-service-price">
                    {fmtEUR(service.price_cents)}
                  </span>

                  <span className="v3-service-chevron">
                    <ArrowUpRight size={19} />
                  </span>

                </button>
              ))}

            </div>

            <div className="v3-services-footnote">
              Prices and service durations are awaiting confirmation.
            </div>

          </div>
        </section>

        {/* ABOUT */}
        <section
          id="about"
          className="v3-section v3-about"
        >
          <div className="v3-container v3-about-layout">

            <div className="v3-about-visual">

              <div className="v3-about-photo">
                <img
                  src={studio.picture}
                  alt="Portrait of Aaron Binions"
                />
              </div>

              <div className="v3-about-detail">
                <span>AB.</span>

                <span>
                  MONASTEREVIN
                  <br />
                  CO. KILDARE
                </span>
              </div>

            </div>

            <div className="v3-about-content">

              <div className="v3-overline">
                ABOUT
              </div>

              <h2>About Me.</h2>

              <p>
                I'm Aaron, a barber based in Monasterevin,
                Co. Kildare, with over six years of experience.
              </p>

              <p>
                I work from my private studio, offering haircuts
                and beard trims by appointment.
              </p>

              <p>
                You can book directly through the website by
                choosing your service and a time that suits you.
              </p>

              <div className="v3-about-details">

                <span>
                  <MapPin size={17} />
                  Monasterevin, Co. Kildare
                </span>

                <span>
                  <Clock3 size={17} />
                  By appointment
                </span>

              </div>

              <a
                href={studio.instagram}
                className="v3-instagram-link"
                target="_blank"
                rel="noreferrer"
              >
                <Instagram size={18} />
                {studio.handle}
                <ArrowUpRight size={15} />
              </a>

            </div>

          </div>
        </section>

        {/* REVIEWS */}
<section
  id="reviews"
  className="v3-section v3-reviews"
>
  <div className="v3-container">

    <div className="v3-section-head">
      <div>
        <div className="v3-overline">
          CLIENT FEEDBACK
        </div>

        <h2>Customer Reviews</h2>
      </div>

   
    </div>

    <div className="v3-review-grid">

      {[
        {
          quote:
            "My fade came out perfectly and the beard trim was exactly what I wanted. Big shout out to Aaron.",
          date: "November 2025",
        },
        {
          quote:
            "Great service. My son is always extremely happy with his hair.",
          date: "April 2025",
        },
        {
          quote:
            "Top notch from Aaron as always, also helped me out with car trouble, top man.",
          date: "May 2025",
        },
      ].map((review, i) => (

        <article
          className="v3-review-card"
          key={i}
        >

          <div className="v3-review-top">
            <span
              className="v3-stars"
              aria-label="5 out of 5 stars"
            >
              ★★★★★
            </span>
          </div>

          <blockquote>
            “{review.quote}”
          </blockquote>

          <div className="v3-review-bottom">
            <span>{review.date}</span>
          </div>

        </article>

      ))}

    </div>

  </div>


  <div className="v3-review-source">
  <span>Reviews shared via my Instagram</span>

  <a
    href={studio.instagram}
    target="_blank"
    rel="noopener noreferrer"
  >
    <Instagram size={16} />
    {studio.handle}
    <ArrowUpRight size={14} />
  </a>
</div>
</section>

        {/* FINAL BOOKING CTA */}
        <section className="v3-last-cta">

          <div className="v3-container v3-last-cta-inner">

            <div>

              <div className="v3-overline">
                APPOINTMENTS
              </div>

              <h2>Book an appointment.</h2>

              <p>
                Choose your service and find a time that suits you.
              </p>

            </div>

            <button
              type="button"
              className="v3-button v3-button-light"
              onClick={() => book()}
            >
              Book appointment
              <ArrowUpRight size={17} />
            </button>

          </div>

        </section>

      </main>

      {/* FOOTER */}
      <footer className="v3-footer">

        <div className="v3-container v3-footer-inner">

          <div className="v3-footer-brand">

            <b>AB.</b>

            <span>
              Aaron Binions · Independent barber
              <br />
              Monasterevin, Co. Kildare
            </span>

          </div>

          <div>

            <a
              href={studio.instagram}
              target="_blank"
              rel="noreferrer"
            >
              Instagram
              <ArrowUpRight size={13} />
            </a>

            <small>
              Full studio address provided privately.
            </small>

          </div>

          <div className="v3-footer-legal">
            © {new Date().getFullYear()} Aaron Binions
            <br />
            Powered by BarberOS
          </div>

        </div>

      </footer>

      {/* BOOKING MODAL */}
      {booking && (
        <BookingFlow
          key={selectedService?.id ?? 'new'}
          data={data}
          initialService={selectedService}
          onClose={() => setBooking(false)}
        />
      )}

      {/* MOBILE BOOKING BUTTON */}
      <button
        type="button"
        className="v3-mobile-book"
        onClick={() => book()}
      >
        Book appointment
        <ArrowUpRight size={16} />
      </button>

    </div>
  );
}