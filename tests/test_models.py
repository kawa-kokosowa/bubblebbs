from bubblebbs import models

class TestPost:
    def test_make_tripcode(self):
        assert ('bleh', 'ZoGgoBAnxOWv8QiHwA9A') == models.Post.make_tripcode('bleh#lol')

    def test_reference_links(self):
        test_links_message = '''
        guess what

        >>22

        ur good

        >>asdf

        >>3

        >dlasjf;lkjsd

        >3

        your >> butt >> 33

        afsoiu wfkj wfe >>22 ajs;lfkjasf>>22

        >>33f
        '''
        hopefully_nicely_linked = models.Post.reference_links(test_links_message, 42)
        correctly_parsed_nicely_linked = '''
        guess what

        <a href="/posts/42#22">&gt;&gt;22</a>

        ur good

        &gt;&gt;asdf

        <a href="/posts/42#3">&gt;&gt;3</a>

        &gt;dlasjf;lkjsd

        &gt;3

        your &gt;&gt; butt &gt;&gt; 33

        afsoiu wfkj wfe <a href="/posts/42#22">&gt;&gt;22</a> ajs;lfkjasf<a href="/posts/42#22">&gt;&gt;22</a>

        <a href="/posts/42#33">&gt;&gt;33</a>f
        '''
        assert hopefully_nicely_linked == correctly_parsed_nicely_linked
