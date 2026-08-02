import { NavLink } from "react-router-dom";

import { HealthIndicator } from "./HealthIndicator";

const navItems: Array<{ to: string; label: string; end?: boolean }> = [
  { to: "/", label: "Home", end: true },
  { to: "/player", label: "Player" },
  { to: "/garden", label: "Garden" },
  { to: "/history", label: "History" },
  { to: "/quests", label: "Quests" },
  { to: "/achievements", label: "Achievements" },
  { to: "/dev-garden", label: "Dev Garden" },
];

export function TopNav() {
  return (
    <header className="top-nav">
      <div className="top-nav__inner">
        <NavLink to="/" className="brand" end>
          <span className="brand__mark" aria-hidden="true">
            ✿
          </span>
          <span className="brand__text">
            <strong>MusicBloom</strong>
            <span>Grow your music garden</span>
          </span>
        </NavLink>

        <nav className="top-nav__links" aria-label="Primary">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                isActive ? "nav-link nav-link--active" : "nav-link"
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="top-nav__status">
          <HealthIndicator />
        </div>
      </div>
    </header>
  );
}
