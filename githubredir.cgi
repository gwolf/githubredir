#!/usr/bin/ruby -I .
# -*- coding: utf-8 -*-
#
# Copyright © 2008-2010 Gunnar Wolf <gwolf@debian.org>
#
# Includes patches by:
#
# Joshua Timberman (March, 2010): Fixed missing tags by querying a slightly
# different pattern
# Stephen Walker (November, 2010): Github changed layout and killed our 
# scraping; Stephen fixed it
############################################################
#             DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
#                     Version 2, December 2004
#
#  Copyright (C) 2004 Sam Hocevar
#   14 rue de Plaisance, 75014 Paris, France
#  Everyone is permitted to copy and distribute verbatim or modified
#  copies of this license document, and changing it is allowed as long
#  as the name is changed.
#
#             DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
#    TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION
#
#   0. You just DO WHAT THE FUCK YOU WANT TO.
#
# http://sam.zoy.org/wtfpl/
############################################################
# What is needed to get this script going?
#
# - Put the following content as a .htaccess (for Apache installations - for
#   other webservers, translate as you see fit):
#
#   Options +ExecCGI
#   <IfModule mod_rewrite.c>
#     RewriteEngine on
#     RewriteRule ^github/([^/\.]+)/([^/\.]+)/?$ githubredir.cgi?author=$1&project=$2 [L]
#     RewriteRule ^github/([^/\.]+)/([^/\.]+)/(.+).tar.gz$ githubredir.cgi?author=$1&project=$2&tag=$3 [L]
#   </IfModule>
require 'rubygems'
require 'open-uri'
require 'cgi'
require 'json'

class GitHubRedir
  def initialize(author, project, tag=nil)
    @project = project[0]
    @author = author[0]
    tag = tag[0] if tag.is_a?(Array)
    @status = :ok
    @result = nil

    if tag.nil? or tag.empty?
      # No tag requested: Generate the index
      begin
	# Fetch the tags, hash them by tagname
        doc_tags = JSON.parse(open(uri_for_tags, 'User-Agent' => 'Githubredir').read)
        releases = Hash[* doc_tags.map{ |tag|
                          [ tag['name'], uri_for_tarball(tag['name']) ]
                        }.flatten]

        @result = html_for_tags(releases)
      rescue RuntimeError, OpenURI::HTTPError => msg
        @result = error_msg_for(msg)
        @status = :fail
      end
    else
      @status = :redirect
      # Substitute '0~master' for 'master' - We added it (see link
      # generation below) to prevent us from robbing uscan's attention
      tag.gsub! /^0~master/, 'master'
      @result = uri_for_download(@author, @project, tag)
    end
  end

  def http_headers
    return {'status' => 'OK'} if @status == :ok
    return {'status' => 'REDIRECT', 'location' => @result} if @status == :redirect
    return {'status' => 'SERVER_ERROR'}
  end

  def result
    '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
<head>
<title>Githubredir - Delivering .tar.gz from Github tags</title>
<link rel="stylesheet" href="/style.css" type="text/css" />
<meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
</head>
<body>
' << @result << '
</body>
</html>
'
  end

  private
  def html_link(uri, text)
    '<a href="%s">%s</a>' % [uri, text]
  end

  def uri_for_tags
    'https://api.github.com/repos/%s/%s/tags' % [@author, @project]
  end

  def uri_for_tarball(tag)
    '/github/%s/%s/%s.tar.gz' % [@author, @project, tag]
  end

  def uri_for_download(author, project, tag)
    'https://github.com/%s/%s/archive/%s.tar.gz' % [author, project, tag]
  end

  def uri_for_author
    'https://github.com/%s' % @author
  end

  def uri_for_project
    'https://github.com/%s/%s' % [@author, @project]
  end

  def html_for_tags(tags)
    raise RuntimeError, 'No tags available' if tags.nil?
    res = ["<h1>Available tags</h1>", proj_info]
    res << '<ul>' << tags.reject {|k,v| k.nil? or k.empty?}.sort.map do |tag, link|
      '<li>%s</li>' % html_link(link, "Download #{tag}")
    end << '</ul>'
    res << redir_description

    res.join("\n")
  end

  def error_msg_for(what)
    "<h1>Error opening project URL</h1>\n" + proj_info +
      "\n<p>#{what}</p>\n" + redir_description
  end

  def proj_info
    auth_link = html_link(uri_for_author, @author)
    proj_link = html_link(uri_for_project, @project)
    master_link = html_link(uri_for_tarball('0~master'), 'Download tar.gz (snapshot)')
    "<p>\n" +
      "Author: #{auth_link}<br/>\n" +
      "Project: #{proj_link}<br/>\n" +
      "Master branch: #{master_link}.<br/>\n" +
      "<em>Master branch is reported as under " +
      "version 0 in order not to disturb proper tags' ordering</em>\n" +
      "</p>"
  end

  def redir_description
    %q(<hr />
<p>
This redirctor is a tool written to ease the automated new
version downloading for automated QA in the Debian system.<br/>
Anybody who finds this system useful can freely use it, although you
might be better served by the rich, official <a
href="https://github.com/">GitHub.com</a> interface.<br/>
For any questions regarding this script, please contact
<a href="mailto:gwolf@debian.org">Gunnar Wolf</a>.
</p>)
  end
end

cgi = CGI.new
params = cgi.params
ghr = GitHubRedir.new(params['author'], params['project'], params['tag'])

cgi.out(ghr.http_headers) { ghr.result }
