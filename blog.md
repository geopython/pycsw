---
layout: default
title: Blog
active_page: blog
---

# Archive [![RSS](/img/rss.png)](http://pycsw.org/feed.xml)

<ul>
  {% for post in site.posts %}
    <li>
      <a href="{{ post.url }}">{{ post.title }}</a>
    </li>
  {% endfor %}
</ul>
