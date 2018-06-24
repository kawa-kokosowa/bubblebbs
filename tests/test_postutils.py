from textwrap import dedent

from bubblebbs import postutils


def test_make_tripcode():
    assert ('bleh', 'CWj74YsG7iMjTMMxPvhZpA--') == postutils.make_tripcode('bleh#lol')


# FIXME: how the heck can i test this when it generates time?
def test_parse_markdown():
    markdown_to_parse = """
	[TOC]

	## Example Markdown Post

	This is an example Markdown post. This is a normal paragraph. Oh look, this paragraph [has a link!](http://example.org)

	*This is a bold paragraph.*

	_This paragraph is italic._

	To use codeblocks just use three of these to open and close: `

	### H3

	Here's some more text and oh look a citation.[^1]

	#### H4

	If you do ... it gets turned into a proper ellipsis.

	The HTML specification
	is maintained by the W3C. This paragraph shows off abbreviations.

	*[HTML]: Hyper Text Markup Language
	*[W3C]:  World Wide Web Consortium

	##### H5

	If use you use " they get turned into left and right quotes.

	Here are some definition lists...

	Apple
	:   Pomaceous fruit of plants of the genus Malus in
	    the family Rosaceae.

	Orange
	:   The fruit of an evergreen tree of the genus Citrus.

	###### H6

	If you use apostrophes ' they get turned into the proper-facing version.

	This is
	a single paragraph
	because of nl2br

	### Citations

	[^1]: A rad person
	"""
    markdown_to_parse = dedent(dedent(markdown_to_parse).strip())

    html_result_hopefully = """
	<ul>
	<li><a href="#example-markdown-post">Example Markdown Post</a><ul>
	<li><a href="#h3">H3</a><ul>
	<li><a href="#h4">H4</a><ul>
	<li><a href="#h5">H5</a><ul>
	<li><a href="#h6">H6</a></li>
	</ul>
	</li>
	</ul>
	</li>
	</ul>
	</li>
	<li><a href="#citations">Citations</a></li>
	</ul>
	</li>
	</ul>

	<h2 id="example-markdown-post">Example Markdown Post</h2>
	<p>This is an example Markdown post. This is a normal paragraph. Oh look, this paragraph <a href="http://example.org">has a link!</a></p>
	<p><em>This is a bold paragraph.</em></p>
	<p><em>This paragraph is italic.</em></p>
	<p>To use codeblocks just use three of these to open and close: `</p>
	<h3 id="h3">H3</h3>
	<p>Here&rsquo;s some more text and oh look a citation.<sup id="fnrefcats-1"><a href="#fncats-1">1</a></sup></p>
	<h4 id="h4">H4</h4>
	<p>If you do &hellip; it gets turned into a proper ellipsis.</p>
	<p>The HTML specification<br>
	is maintained by the W3C. This paragraph shows off abbreviations.</p>
	<h5 id="h5">H5</h5>
	<p>If use you use &rdquo; they get turned into left and right quotes.</p>
	<p>Here are some definition lists&hellip;</p>
	<dl>
	<dt>Apple</dt>
	<dd>Pomaceous fruit of plants of the genus Malus in<br>
	the family Rosaceae.</dd>
	<dt>Orange</dt>
	<dd>The fruit of an evergreen tree of the genus Citrus.</dd>
	</dl>
	<h6 id="h6">H6</h6>
	<p>If you use apostrophes &lsquo; they get turned into the proper-facing version.</p>
	<p>This is<br>
	a single paragraph<br>
	because of nl2br</p>
	<h3 id="citations">Citations</h3>


	<ol>
	<li id="fncats-1">
	<p>A rad person?qq3936677670287331zz?<a href="#fnrefcats-1">?zz1337820767766393qq?</a></p>
	</li>
	</ol>
	"""
    html_result_hopefully = dedent(html_result_hopefully).strip()

    assert postutils.parse_markdown(markdown_to_parse, unique_slug='cats') == html_result_hopefully


def test_add_domains_to_link_texts():
    message_to_parse = """
    Have you read <a href="http://www.example.org/somebook.pdf" class="heck">Some Book</a>?
    I thought it was similar to <a href="/downloads/anotherbook.pdf">Another
    Book</a>, which is hosted on this website.
    """.strip()
    parsed_message = """
    Have you read <a class="heck external-link" href="http://www.example.org/somebook.pdf">Some Book (www.example.org)</a>?
    I thought it was similar to <a class="internal-link" href="/downloads/anotherbook.pdf">Another
    Book (internal link)</a>, which is hosted on this website.
    """.strip()

    assert postutils.add_domains_to_link_texts(message_to_parse) == parsed_message
