import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "jsr:@supabase/supabase-js@2"

// 🔥 SAME AI ENGINE YOU USED FOR JOBS
const model = new Supabase.ai.Session("gte-small")

serve(async (req) => {
  try {
    const { resume_id, skills, feedback, score } = await req.json()

    if (!resume_id) {
      return new Response("Missing resume_id", { status: 400 })
    }

    // 🧠 Build structured embedding text
    const text = `
Skills: ${(skills || []).join(", ")}
Feedback: ${JSON.stringify(feedback || {})}
Score: ${score || 0}
`

    // 🧠 Generate embedding (SAME as jobs)
    const result = await model.run(text, {
      mean_pool: true,
      normalize: true,
    })

    // ⭐ Convert TypedArray → Array
    const embedding = Array.from(result)

    // 🔐 Service role client
    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
    )

    // ⭐ Update resumes table
    const { error } = await supabase
      .from("resumes")
      .update({ embedding })
      .eq("id", resume_id)

    if (error) throw error

    return new Response(JSON.stringify({ success: true }), {
      headers: { "Content-Type": "application/json" },
    })

  } catch (err) {
    console.error("EDGE ERROR:", err)
    return new Response(
      JSON.stringify({ error: err.message }),
      { status: 500 }
    )
  }
})