---
layout: default
title: Blog
active_page: blog
---

# Archive [![RSS]({{site.url}}/img/rss.png)]({{site.url}}/blog/feed.xml)

<ul>
  {% for post in site.posts %}
    <li>
      <a href="{{site.url}}{{ post.url }}">{{ post.title }}</a>
    </li>
  {% endfor %}
</ul>
