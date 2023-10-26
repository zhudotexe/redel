export function greekLetter(name: string): string {
  switch (name.toLowerCase()) {
    case "alpha":
      return "α";
    case "beta":
      return "β";
    case "gamma":
      return "γ";
    case "delta":
      return "δ";
    case "epsilon":
      return "ϵ";
    case "zeta":
      return "ζ";
    case "eta":
      return "η";
    case "theta":
      return "θ";
    case "iota":
      return "ι";
    case "kappa":
      return "κ";
    case "lambda":
      return "λ";
    case "mu":
      return "μ";
    case "nu":
      return "ν";
    case "xi":
      return "ξ";
    case "omicron":
      return "Ο";
    case "pi":
      return "π";
    case "rho":
      return "ρ";
    case "sigma":
      return "σ";
    case "tau":
      return "τ";
    case "upsilon":
      return "υ";
    case "phi":
      return "ϕ";
    case "chi":
      return "χ";
    case "psi":
      return "ψ";
    case "omega":
      return "ω";
    default:
      return name;
  }
}
