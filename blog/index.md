---
layout: default
title: Blog
active_page: blog
---

# Archive [![RSS]({{site.baseurl}}/img/rss.png)]({{site.baseurl}}/blog/feed.xml)

<ul>
  {% for post in site.posts %}
    <li>
      <a href="{{site.baseurl}}{{ post.url }}">{{ post.title }}</a>
    </li>
  {% endfor %}
</ul>
