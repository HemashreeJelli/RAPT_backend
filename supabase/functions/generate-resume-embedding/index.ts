import { serve } from "https://deno.land/std/http/server.ts";

serve(async (req) => {
  try {
    const { resume_id, skills, feedback, score } = await req.json();

    if (!resume_id) {
      throw new Error("Missing resume_id");
    }

    // ⭐ Build embedding text
    const text = `
Skills: ${(skills || []).join(", ")}
Feedback: ${JSON.stringify(feedback || {})}
Score: ${score || 0}
`;

    // ⭐ Generate embedding using Supabase SQL AI
    const embedRes = await fetch(
      `${Deno.env.get("SUPABASE_URL")}/rest/v1/rpc/ai_embed`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")}`,
          apikey: Deno.env.get("SUPABASE_SERVICE_ROLE_KEY"),
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: "gte-small",
          input: text,
        }),
      }
    );

    const embedData = await embedRes.json();

    console.log("EMBED RESPONSE:", embedData);

    if (!embedData || !embedData.embedding) {
      throw new Error("Embedding API returned invalid response");
    }

    const embedding = embedData.embedding;

    // ⭐ Update resumes table
    await fetch(
      `${Deno.env.get("SUPABASE_URL")}/rest/v1/resumes?id=eq.${resume_id}`,
      {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")}`,
          apikey: Deno.env.get("SUPABASE_SERVICE_ROLE_KEY"),
          "Content-Type": "application/json",
          Prefer: "return=minimal",
        },
        body: JSON.stringify({
          embedding: embedding,
        }),
      }
    );

    return new Response(JSON.stringify({ success: true }), { status: 200 });

  } catch (err) {
    console.log("EDGE ERROR:", err);
    return new Response(err.message, { status: 500 });
  }
});