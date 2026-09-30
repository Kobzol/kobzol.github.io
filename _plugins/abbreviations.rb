# Appends kramdown abbreviation definitions (`*[PGO]: Profile-Guided Optimization`)
# from `abbreviations.txt` to every post, unless the post already defines them itself.
Jekyll::Hooks.register :posts, :pre_render do |doc|
  next unless doc.extname =~ /\.(md|markdown)$/
  path = File.join(doc.site.source, "abbreviations.txt")
  next unless File.exist?(path)

  definitions = File.readlines(path, chomp: true).filter_map do |line|
    line = line.strip
    next if line.empty? || line.start_with?("#")
    abbr, explanation = line.split(": ", 2)
    next if explanation.nil?
    next if doc.content =~ /^\*\[#{Regexp.escape(abbr)}\]:/
    "*[#{abbr}]: #{explanation}"
  end
  doc.content = doc.content.rstrip + "\n\n" + definitions.join("\n") + "\n" unless definitions.empty?
end
