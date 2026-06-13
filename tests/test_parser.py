from slough.models import TestCase
from slough.parser import parse_md_examples, parse_example_lines


def test_parse_simple_example():
    md = """
## Example 1:

Input: nums = [2,7,11,15], target = 9
Output: [0,1]

## Example 2:

Input: nums = [3,2,4], target = 6
Output: [1,2]

## Example 3:

Input: nums = [3,3], target = 6
Output: [0,1]
    """
    cases = parse_md_examples(md)
    assert len(cases) == 3
    assert cases[0].inputs == ([2, 7, 11, 15], 9)
    assert cases[0].expected == [0, 1]
    assert cases[1].inputs == ([3, 2, 4], 6)
    assert cases[1].expected == [1, 2]
    assert cases[2].inputs == ([3, 3], 6)
    assert cases[2].expected == [0, 1]


def test_parse_with_strings():
    md = """
## Example 1:

Input: s = "hello", t = "world"
Output: "helloworld"
    """
    cases = parse_md_examples(md)
    assert len(cases) == 1
    assert cases[0].inputs == ("hello", "world")
    assert cases[0].expected == "helloworld"


def test_parse_with_boolean_and_none():
    md = """
## Example:

Input: root = [1,2,3], p = 5, q = None
Output: true
    """
    cases = parse_md_examples(md)
    assert len(cases) == 1
    assert cases[0].inputs[-1] is None
    # p=5 should be int


def test_parse_no_output():
    """If no Output: line, expected should be None."""
    md = """
## Example 1:

Input: x = 5
    """
    cases = parse_md_examples(md)
    assert len(cases) == 1
    assert cases[0].inputs == (5,)
    assert cases[0].expected is None


def test_parse_empty_md():
    cases = parse_md_examples("")
    assert cases == []


def test_parse_no_examples():
    cases = parse_md_examples("# Just a title\nNo examples here")
    assert cases == []


def test_parse_example_lines_basic():
    result = parse_example_lines(
        "Input: nums = [2,7,11,15], target = 9",
        "Output: [0,1]",
    )
    assert result == TestCase(inputs=([2, 7, 11, 15], 9), expected=[0, 1])


def test_parse_example_lines_strings():
    result = parse_example_lines(
        'Input: s = "hello"',
        'Output: "olleh"',
    )
    assert result.inputs == ("hello",)
    assert result.expected == "olleh"


def test_parse_example_lines_no_output():
    result = parse_example_lines("Input: x = 42", None)
    assert result.inputs == (42,)
    assert result.expected is None


def test_parse_with_negative_numbers():
    md = """
## Example:

Input: nums = [-1,-2,-3], target = -4
Output: [0,2]
    """
    cases = parse_md_examples(md)
    assert cases[0].inputs == ([-1, -2, -3], -4)
    assert cases[0].expected == [0, 2]


def test_parse_example_lines_with_only_input():
    result = parse_example_lines("Input: root = [1,2,3], depth = 0", None)
    assert result.inputs == ([1, 2, 3], 0)


def test_parse_html_format_same_line_pre():
    """12-integer-to-roman style: <pre><strong>Input:</strong> on same line, literal quotes."""
    md = """
<p><strong>Example 1:</strong></p>
<pre><strong>Input:</strong> num = 3
<strong>Output:</strong> "III"
<strong>Explanation:</strong> 3 is represented as 3 ones.
</pre>

<p><strong>Example 2:</strong></p>
<pre><strong>Input:</strong> num = 58
<strong>Output:</strong> "LVIII"
<strong>Explanation:</strong> L = 50, V = 5, III = 3.
</pre>

<p><strong>Example 3:</strong></p>
<pre><strong>Input:</strong> num = 1994
<strong>Output:</strong> "MCMXCIV"
<strong>Explanation:</strong> M = 1000, CM = 900, XC = 90 and IV = 4.
</pre>
    """
    cases = parse_md_examples(md)
    assert len(cases) == 3
    assert cases[0].inputs == (3,)
    assert cases[0].expected == "III"
    assert cases[1].inputs == (58,)
    assert cases[1].expected == "LVIII"
    assert cases[2].inputs == (1994,)
    assert cases[2].expected == "MCMXCIV"


def test_parse_html_format_new_line_pre_with_entities():
    """0003-longest-substring style: <pre> on own line, class='example', &quot; entities."""
    md = """
<p><strong class="example">Example 1:</strong></p>
<pre>
<strong>Input:</strong> s = &quot;abcabcbb&quot;
<strong>Output:</strong> 3
<strong>Explanation:</strong> The answer is &quot;abc&quot;, with the length of 3.
</pre>

<p><strong class="example">Example 2:</strong></p>
<pre>
<strong>Input:</strong> s = &quot;bbbbb&quot;
<strong>Output:</strong> 1
</pre>

<p><strong class="example">Example 3:</strong></p>
<pre>
<strong>Input:</strong> s = &quot;pwwkew&quot;
<strong>Output:</strong> 3
</pre>
    """
    cases = parse_md_examples(md)
    assert len(cases) == 3
    assert cases[0].inputs == ("abcabcbb",)
    assert cases[0].expected == 3
    assert cases[1].inputs == ("bbbbb",)
    assert cases[1].expected == 1
    assert cases[2].inputs == ("pwwkew",)
    assert cases[2].expected == 3


def test_parse_html_with_img_tags():
    """0206-reverse-linked-list style: <img> between heading and <pre>."""
    md = """
<p><strong class="example">Example 1:</strong></p>
<img alt="" src="https://example.com/img.jpg" />
<pre>
<strong>Input:</strong> head = [1,2,3,4,5]
<strong>Output:</strong> [5,4,3,2,1]
</pre>

<p><strong class="example">Example 2:</strong></p>
<img alt="" src="https://example.com/img2.jpg" />
<pre>
<strong>Input:</strong> head = [1,2]
<strong>Output:</strong> [2,1]
</pre>
    """
    cases = parse_md_examples(md)
    assert len(cases) == 2
    assert cases[0].inputs == ([1, 2, 3, 4, 5],)
    assert cases[0].expected == [5, 4, 3, 2, 1]
    assert cases[1].inputs == ([1, 2],)
    assert cases[1].expected == [2, 1]


def test_parse_html_without_class():
    """HTML format with <p><strong> (no class='example')."""
    md = """
<p><strong>Example 1:</strong></p>
<pre><strong>Input:</strong> nums = [1,2,3], target = 4
<strong>Output:</strong> [0,2]
</pre>
    """
    cases = parse_md_examples(md)
    assert len(cases) == 1
    assert cases[0].inputs == ([1, 2, 3], 4)
    assert cases[0].expected == [0, 2]


def test_parse_html_two_outputs_takes_first():
    """1-two-sum style: Example 1 has two Output: lines. Should take first."""
    md = """
<p><strong>Example 1:</strong></p>
<pre><strong>Input:</strong> nums = [2,7,11,15], target = 9
<strong>Output:</strong> [0,1]
<strong>Output:</strong> Because nums[0] + nums[1] == 9, we return [0, 1].
</pre>
    """
    cases = parse_md_examples(md)
    assert len(cases) == 1
    assert cases[0].inputs == ([2, 7, 11, 15], 9)
    assert cases[0].expected == [0, 1]


def test_parse_markdown_still_works_after_html_changes():
    """Original markdown format must not regress."""
    md = """
## Example 1:

Input: nums = [2,7,11,15], target = 9
Output: [0,1]
    """
    cases = parse_md_examples(md)
    assert len(cases) == 1
    assert cases[0].inputs == ([2, 7, 11, 15], 9)
    assert cases[0].expected == [0, 1]
