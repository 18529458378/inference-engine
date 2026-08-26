---
name: control-in-app-browser
description: >-
  Control the current chat's in-app Browser for opening, navigating, inspecting visible or
  interactive page state, clicking, typing, screenshots, and local web testing. It can have an
  existing signed-in session. Explicit requests for the in-app, embedded, right-side, current, or
  FilePanel Browser use this skill; for linked resources without explicit Browser intent, prefer a
  purpose-built connector, API, or CLI when available.
requiresBeta: browserUseTooling
descriptions:
  zh-Hans:
    '控制当前会话右侧的内置 Browser。用户明确要求查看或操作内置浏览器、右侧浏览器、当前浏览器或
    browser use 时必须加载。'
displayNames:
  zh-Hans: '控制内置浏览器'
---

# Control In-App Browser

Use the native `browser` tool to inspect and operate the Browser tab in the current chat's
right-side FilePanel.

When this skill is listed and the user explicitly requests this Browser surface, read and follow it
before the first native Browser action. Do not infer that unrelated skills may be loaded implicitly.

## Choose The Browser Surface

Explicit Browser intent wins. If the user names the in-app, embedded, right-side, current, or
FilePanel Browser, or says `browser use`, continue with this skill and the native `browser` tool. Do
not substitute a connector, CLI, standalone Playwright browser, or Computer Use.

App-provided in-app-browser context is ambient UI state, not Browser intent. Only the user's request
can explicitly select this Browser surface. A visible Browser tab by itself does not require a
Browser action.

A URL or linked resource without explicit Browser intent is different. In that case, prefer a
purpose-built connector, API, or CLI when one is available. For example, a Feishu URL alone may use
the Lark document tools; "read this in the right-side Browser" must use this Browser skill.

## Browser Identity

The native `browser` tool controls the FilePanel Browser owned by the current chat session. It is
not a separate remote browser and not a separate Playwright browser. The runtime supplies the
authoritative session ID and resolves that session's selected embedded tab.

The selected tab may contain an existing signed-in session. Use that page state only to complete the
requested UI task; never inspect or expose authentication material.

Never tell the user that this tool cannot see the right-side Browser because it is a different
browser instance. Do not switch to desktop screenshots merely to reach the FilePanel Browser.

## Start With Inspect

When the user refers to a page or content already open in the Browser, the first call must be:

```text
browser({ action: "inspect", input: {} })
```

`inspect` returns the current URL, title, page state, snapshot ID, and actionable opaque element
refs. Do not ask the user to provide the URL or a screenshot before trying `inspect`.

If the result has `truncated: true`, continue the same snapshot with its `snapshotId` and
`nextOffset`. Do not start a new snapshot until the current one is exhausted or the page changes.

## Read Page Content With Query

`query` reads page content that is not represented by the actionable-element snapshot. It always
requires an explicit `input.kind`; never call `query` with an empty input.

Use `kind: "text"` for visible page text and narrow the selector when possible:

```text
browser({ action: "query", input: { kind: "text", selector: "body", maxChars: 20000 } })
```

Use `kind: "dom"` only when markup is required, and `kind: "editable"` to discover editable targets.
Use `inspect`, not an empty or implicit `query`, for the normal actionable-element snapshot and its
pagination.

## Operation Loop

1. `inspect` the current tab.
2. Choose an opaque element ref or an action supported by the compact Browser schema.
3. Call `browser` with the selected `action` and only that action's `input` fields.
4. Verify the result with `inspect`, `query`, or `screenshot` when visual confirmation matters.

Navigation and interaction actions return short status metadata, not a fresh page snapshot. Call
`inspect` or `query` explicitly when page details are needed after an action. Do not expect
`browserState`, ElementMap indices, or local map paths in compact action results.

Every `click`, `double_click`, `hover`, `drag`, `fill`, `type`, `check`, `uncheck`, and
`select_option` target must use a valid `ref`, `selector`, or `index`; pointer actions may also use
`normalized_position`. `check`, `uncheck`, and `select_option` do not accept coordinates. `fill`
always clears before entering text; use `type` when clear and per-key delay behavior must be chosen.

Use `navigate` only when the user supplied a destination or explicitly asked to open another page.
Use `screenshot` when visual layout matters; do not use it as a substitute for structured
inspection.

Element and frame refs are snapshot-scoped. After navigation, reload, or a stale-ref error, call
`inspect` again instead of reusing an old ref.

## Safety And Recovery

- Arbitrary JavaScript execution is unavailable and must not be simulated through another tool.
- Do not inspect cookies, local storage, passwords, profiles, or authentication secrets.
- A read request must not trigger clicks, typing, navigation, or other side effects.
- If an action fails validation, correct its `input` using the action contract; do not reinterpret
  validation failure as evidence that the Browser is a different instance.
- Report Browser unavailability only when the native tool is absent or returns an explicit disabled
  or unavailable error after an attempted call.

Once this skill has been loaded for the current task, keep using the existing Browser context; do
not reload the skill on every action.
