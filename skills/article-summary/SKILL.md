---
name: article-summary
description: Summarize a user-provided article, public URL, webpage, PDF, Word document, or text in the original order. Use for Chinese requests such as "总结一下", "告诉我这篇文章讲了什么", "概括这篇文章", "帮我总结这篇", or equivalent requests in any language. Map key points to original sections or paragraphs, audit factual accuracy and ambiguity, and create a PDF only when the user explicitly asks for an exported document or PDF.
---

# Article Summary

## Workflow

1. Identify the exact source and read the original before summarizing.
   - For public URLs, use the authoritative page.
   - For local PDFs or Word documents, use the relevant document skill and inspect the actual file.
   - If access is blocked by a login, CAPTCHA, paywall, or missing attachment, ask the user to provide access or the document. Do not fill gaps with search snippets or assumptions.
2. Extract 5-12 core points, scaled to the source length. Preserve the order in which they appear in the source; do not rearrange them into a topical order.
3. For every point, provide:
   - A concise conclusion.
   - `对应原文位置` with a link anchor, heading, page number, or paragraph identifier that lets the user locate the source.
   - `原文段落摘译` as a faithful Chinese paraphrase. Use only short quotations when needed; do not reproduce long copyrighted passages.
4. Finish with `全文概括总结`: one short paragraph explaining the article's central thesis, mechanism, and conclusion.
5. Audit the draft against the original before delivery. Correct or qualify claims that could be misleading:
   - distinguish announcements, previews, releases, and future plans;
   - distinguish reported metrics from independently verified results;
   - retain stated access restrictions, target audiences, caveats, and ownership of statistics;
   - distinguish participation, commitments, pilots, and completed outcomes;
   - remove unsupported causal claims or interpretations.

## Default response format

Use this structure unless the user asks for a shorter format:

```markdown
1. **核心观点**

   对应原文位置：[章节标题](source-link-or-location)

   原文段落摘译：...

...

## 全文概括总结

...

## 校对说明

说明已核对的限定条件或已修正的歧义；若无重要修正，简短说明“未发现会改变结论的出入”。
```

Use the user's language. Keep prose concrete and separate the source's assertions from your analysis.

## PDF deliverables

Create a PDF only when the user explicitly asks to export, generate, save, or deliver a PDF/document.

1. Use the `pdf` skill and follow its rendering and visual-verification requirements.
2. Put the summary, source locations, overall conclusion, and audit notes in the PDF.
3. Use a font that supports the document language, render every page to images, and fix clipping, broken links, unreadable text, or poor page breaks before delivery.
4. Save the final artifact only in the workspace's designated user-facing output directory, then link it in the final response.
