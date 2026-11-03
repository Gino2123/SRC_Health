"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";

export default function SubscribePage() {
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    const formData = new FormData(event.currentTarget);
    const email = String(formData.get("email"));
    const password = String(formData.get("password"));
    const passwordConfirmation = String(formData.get("passwordConfirmation"));

    if (password !== passwordConfirmation) {
      setError("Les mots de passe ne correspondent pas.");
      return;
    }

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/auth/register`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        },
      );

      if (!response.ok) {
        const body = (await response.json()) as { detail?: string };
        setError(body.detail ?? "La création du compte a échoué.");
        return;
      }

      setSuccess(true);
    } catch {
      setError("Impossible de joindre le serveur. Vérifiez que l’API est démarrée.");
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-50 px-6 py-12">
      <section className="w-full max-w-md rounded-2xl bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">
          Health V1
        </p>
        <h1 className="mt-3 text-3xl font-semibold text-zinc-900">
          Créer un compte
        </h1>
        <p className="mt-2 text-sm text-zinc-600">
          Inscrivez-vous avec votre adresse e-mail et un mot de passe.
        </p>

        {success ? (
          <p
            className="mt-6 rounded-lg bg-teal-50 p-4 text-sm text-teal-900"
            role="status"
          >
            Votre compte a été créé. Vous pouvez maintenant{" "}
            <Link className="font-semibold underline" href="/login">
              vous connecter
            </Link>
            .
          </p>
        ) : (
          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            <label className="block text-sm font-medium text-zinc-700">
              Adresse e-mail
              <input
                autoComplete="email"
                className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2"
                name="email"
                required
                type="email"
              />
            </label>
            <label className="block text-sm font-medium text-zinc-700">
              Mot de passe (12 caractères minimum)
              <input
                autoComplete="new-password"
                className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2"
                minLength={12}
                maxLength={128}
                name="password"
                required
                type="password"
              />
            </label>
            <label className="block text-sm font-medium text-zinc-700">
              Confirmer le mot de passe
              <input
                autoComplete="new-password"
                className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2"
                minLength={12}
                maxLength={128}
                name="passwordConfirmation"
                required
                type="password"
              />
            </label>
            {error && (
              <p className="text-sm text-red-700" role="alert">
                {error}
              </p>
            )}
            <button
              className="w-full rounded-lg bg-teal-700 px-4 py-3 font-medium text-white hover:bg-teal-800"
              type="submit"
            >
              Créer mon compte
            </button>
            <p className="text-center text-sm text-zinc-600">
              Vous avez déjà un compte ?{" "}
              <Link className="font-medium text-teal-700 underline" href="/login">
                Se connecter
              </Link>
            </p>
          </form>
        )}
      </section>
    </main>
  );
}
