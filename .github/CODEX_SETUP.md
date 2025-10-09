# Codex PR Review Setup

This repo uses **OpenAI Codex** (via ChatGPT integration) to automatically review pull requests. No API key needed!

## One-Time Setup (5 minutes)

### Step 1: Connect GitHub to ChatGPT

1. Go to [ChatGPT Settings](https://chatgpt.com/)
2. Click **Settings → Connectors → GitHub**
3. Click **Connect** and authorize this repository
4. ✅ Done! ChatGPT can now access your PRs

📖 [Full instructions](https://help.openai.com/en/articles/11145903-connecting-github-to-chatgpt)

### Step 2: Enable Codex Code Review on This Repo

1. Go to [OpenAI Developers - Code Review](https://developers.openai.com/codex/cloud/code-review/)
2. Enable **"Code review"** for this repository
3. ✅ Done! Codex will now respond to review requests

### Step 3: Verify Your ChatGPT Plan

Codex requires one of these plans:
- ✅ ChatGPT Plus ($20/month)
- ✅ ChatGPT Pro ($200/month)
- ✅ ChatGPT Team
- ✅ ChatGPT Enterprise

Check your plan: [ChatGPT Pricing](https://chatgpt.com/pricing)

---

## How It Works

### Automatic Reviews (Current Setup)

When you open or update a PR, GitHub Actions automatically posts:

```
@codex review

Please review this PR focusing on:
- Code Quality: SOLID principles, DRY violations, type hints
- Bugs & Edge Cases: Potential issues, security concerns
- Cost Optimization: Opportunities to reduce LLM API costs
- Idempotency: Verify operations are safe to re-run
- Project Guidelines: Check adherence to CLAUDE.md principles
```

Codex will then review the PR and post detailed feedback as a **proper GitHub review** (not just a comment).

### Manual Reviews

You can also manually request reviews by commenting on any PR:

```
@codex review
```

Or with custom instructions:

```
@codex review this for security vulnerabilities
```

---

## What Codex Reviews For (Media Digest Specific)

Codex is configured to focus on:

1. **Cost Optimization** - We target $15/month, so any LLM API waste matters
2. **Idempotency** - All operations must be safe to re-run
3. **Type Safety** - Python 3.11+ with full type hints
4. **SOLID Principles** - Single responsibility, DRY, protocols over concrete classes
5. **Project Guidelines** - Adherence to `CLAUDE.md` best practices

---

## Troubleshooting

### "Codex didn't review my PR"

1. Check that GitHub is connected: [ChatGPT Settings](https://chatgpt.com/)
2. Verify code review is enabled: [Codex Code Review](https://developers.openai.com/codex/cloud/code-review/)
3. Make sure you have ChatGPT Plus/Pro/Team/Enterprise
4. Try manually commenting `@codex review` on the PR

### "Codex review is too generic"

Add more specific instructions in your comment:

```
@codex review

Focus specifically on:
- DuckDB query performance
- Whisper transcription error handling
- Claude API cost optimization
```

### "I want to disable auto-reviews"

Delete or disable `.github/workflows/pr-review.yml`

You can still manually trigger reviews by commenting `@codex review`

---

## Cost Comparison

| Approach | Cost | Setup |
|----------|------|-------|
| **Codex GitHub Integration** (current) | $0 extra (uses ChatGPT plan) | 5 min |
| API-based (openai/codex-action) | ~$1-5/month per repo | 10 min + API key |
| GPT-4 API (custom script) | ~$2-10/month | 15 min + API key |

**Winner:** GitHub integration. Zero extra cost, faster reviews, better integration.

---

## Advanced: Custom Prompts

Edit `.github/workflows/pr-review.yml` to customize the review focus:

```yaml
body: `@codex review

Focus on PostgreSQL query optimization and index usage`
```

---

## Resources

- [Codex Documentation](https://developers.openai.com/codex/)
- [GitHub Integration Guide](https://help.openai.com/en/articles/11145903-connecting-github-to-chatgpt)
- [Codex Pricing](https://chatgpt.com/pricing)
- [Media Digest Development Guidelines](./CLAUDE.md)
