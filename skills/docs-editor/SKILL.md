---
name: "docs-editor"
description: "Use when the user asks to edit a Feishu Document, insert elements, or modify specific text in a document. The agent should use keyboard shortcuts for precision instead of mouse clicks."
---

# Docs Editor Skill

Provide robust guidance for document editing workflows in Feishu Docs.

## Trigger

Use this skill when the user intent is equivalent to:
- 在文档中的 xxx 后面补充内容
- 在文档里插入一个表格/图片/待办
- 把文档中的 xxx 改为 yyy

## Workflow

To avoid inaccurate mouse clicks in a free-form canvas like Feishu Docs, this skill enforces a **Keyboard-Driven** approach.

### 1. Anchor Search (精准定位文本)
If you need to edit or append content near specific text:
1. Press `ctrl+f` (or `cmd+f` on Mac) to open the document search box.
2. Input the target text to search. The cursor will automatically jump to the target.
3. Press `esc` to close the search box.
4. Press `right` arrow key to unselect the highlighted text and place the cursor at the end of the text.
5. Input your new text.

### 2. Slash Command (精准插入元素)
If you need to insert complex elements (tables, code blocks, images, todos):
1. Locate the correct position (using Anchor Search or arrow keys).
2. Input `/` to trigger the shortcut menu.
3. Input the element name (e.g., `表格`, `待办`).
4. Press `enter`.

## ReAct constraints

- **ABSOLUTELY FORBIDDEN**: Do not try to use `click_position` to precisely click on a specific word or sentence in the document editing area. Visual coordinates are too inaccurate for text editing.
- Always prefer `press_key` and `paste_content` (or `input_text`) for document operations.
- Selecting text should be done via `shift + arrow keys` rather than mouse dragging.
