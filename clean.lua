-- Pandoc Lua Filter to clean up Cocoa HTML Writer artifacts and enhance structure

function Header(el)
  if el.attributes then
    el.attributes.style = nil
  end
  return el
end

function Para(el)
  local text = pandoc.utils.stringify(el)

  -- Discard empty paragraphs containing only whitespace or line breaks
  if text:match("^%s*$") then
    local has_content = false
    pandoc.walk_block(el, {
      Image = function(_) has_content = true end,
      Link = function(_) has_content = true end
    })
    if not has_content then
      return {}
    end
  end

  -- Wrap "Rule of thumb:" paragraphs in a callout container
  if text:match("^Rule of thumb:") then
    return pandoc.Div({ el }, { class = "rule-of-thumb" })
  end

  -- Detect dialogue lines (e.g. Son:, Mom:, You:, Them:)
  local has_speaker = false
  pandoc.walk_block(el, {
    Span = function(span)
      if span.classes:includes("s1") or span.classes:includes("s2") or span.classes:includes("s3") then
        span.classes:insert("speaker")
        has_speaker = true
      end
    end
  })
  if has_speaker then
    return pandoc.Div({ el }, { class = "dialogue" })
  end

  return el
end

function Span(el)
  if el.attributes then
    el.attributes.style = nil
  end
  -- Drop empty anchor spans leftover from epub XHTML slice files
  if #el.content == 0 and (el.identifier:match("%.xhtml") or el.classes:includes("Apple-converted-space")) then
    return {}
  end
  return el
end

function Strong(el)
  if #el.content == 0 then
    return {}
  end
  return el
end

function Emph(el)
  if #el.content == 0 then
    return {}
  end
  return el
end
