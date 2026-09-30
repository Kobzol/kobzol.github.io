# Expands `[repo#123]` into a link to https://github.com/rust-lang/repo/pull/123,
# and `[org/repo#123]` into `[repo#123]` linking to https://github.com/org/repo/pull/123.
Jekyll::Hooks.register [:posts, :pages], :pre_render do |doc|
  next unless doc.extname =~ /\.(md|markdown)$/
  # Split out fenced and inline code so it is left untouched.
  parts = doc.content.split(/(```.*?```|`[^`\n]*`)/m)
  doc.content = parts.each_with_index.map do |part, i|
    next part if i.odd? # captured code segment
    part.gsub(/\[(?:([A-Za-z0-9_.-]+)\/)?([A-Za-z0-9_.-]+)#(\d+)\](?![(\[:])/) do
      org = $1 || "rust-lang"
      "[#{$2}##{$3}](https://github.com/#{org}/#{$2}/pull/#{$3})"
    end
  end.join
end
