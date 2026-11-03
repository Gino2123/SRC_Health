"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { FormEvent, useState } from "react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    const formData = new FormData(event.currentTarget);
    try {
      const response = await fetch(`${apiUrl}/auth/login`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-Auth-Transport": "cookie",
        },
        body: JSON.stringify({
          email: String(formData.get("email")),
          password: String(formData.get("password")),
        }),
      });

      if (!response.ok) {
        const body = (await response.json()) as { detail?: string };
        setError(body.detail ?? "La connexion a échoué.");
        return;
      }

      let currentUserResponse = await fetch(`${apiUrl}/auth/me`, {
        credentials: "include",
      });
      if (currentUserResponse.status === 401) {
        const refreshResponse = await fetch(`${apiUrl}/auth/refresh`, {
          method: "POST",
          credentials: "include",
          headers: { "X-Auth-Transport": "cookie" },
        });
        if (refreshResponse.ok) {
          currentUserResponse = await fetch(`${apiUrl}/auth/me`, {
            credentials: "include",
          });
        }
      }
      if (!currentUserResponse.ok) {
        setError("La connexion a été acceptée, mais la session n’a pas pu être vérifiée.");
        return;
      }

      router.replace("/home");
    } catch {
      setError("Impossible de joindre le serveur. Vérifiez que l’API est démarrée.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-50 px-6 py-12">
      <section className="w-full max-w-md rounded-2xl bg-white p-8 shadow-sm">
        <Link
          className="text-sm font-semibold uppercase tracking-wide text-teal-700"
          href="/home"
        >
          Health V1
        </Link>
        <h1 className="mt-3 text-3xl font-semibold text-zinc-900">Connexion</h1>
        <>
            <p className="mt-2 text-sm text-zinc-600">
              Saisissez l’adresse e-mail et le mot de passe de votre compte.
            </p>
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
                Mot de passe
                <input
                  autoComplete="current-password"
                  className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2"
                  maxLength={128}
                  name="password"
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
                className="w-full rounded-lg bg-teal-700 px-4 py-3 font-medium text-white hover:bg-teal-800 disabled:opacity-60"
                disabled={isSubmitting}
                type="submit"
              >
                {isSubmitting ? "Connexion…" : "Se connecter"}
              </button>
            </form>
            <p className="mt-4 text-center text-sm text-zinc-600">
              Pas encore de compte ?{" "}
              <Link className="font-medium text-teal-700 underline" href="/subscribe">
                S’inscrire
              </Link>
            </p>
        </>
      </section>
    </main>
  );
}
