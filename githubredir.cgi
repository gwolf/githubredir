#!/usr/bin/ruby -I .
#
# Copyright © 2008 Gunnar Wolf <gwolf@debian.org>
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
#     RewriteRule ^github/([^/\.]+)/([^/\.]+)/([^/]+).tar.gz$ githubredir.cgi?author=$1&project=$2&tag=$3 [L]
#   </IfModule>
#
# - Get Hpricot installed. If your does not provide it, just put it in any 
#   directory under your control, and put it towards the end of Ruby's include
#   path. This can be done by specifying this directory with the -I switch to Ruby.
require 'open-uri'
require 'cgi'
require 'hpricot'

class GitHubRedir
  def initialize(author, project, tag=nil)
    @project = project
    @author = author
    @status = :ok
    @result = nil

    if tag.nil? or tag.empty?
      begin
        # Get the latest available tag (version)
        doc = Hpricot(open(index_uri))
        releases = []

        rels = doc / '#other_archives' / 'li'
        raise RuntimeError, 'No releases found' if rels.empty?

        rels.each do |li|
          ver = (li/'a').text
          releases << ver
        end
        @result = html_for_tags(releases)
      rescue RuntimeError, OpenURI::HTTPError => msg
        @result = error_msg_for(msg)
        @status = :fail
      end
    else
      @status = :redirect
      @result = 'http://github.com/%s/%s/tarball/%s' % [@author, @project, tag]
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
<body>' << @result << '</body></html>'
  end

  private
  def index_uri(branch='master')
    'http://github.com/%s/%s/archives/%s' % [@author, @project, branch]
  end

  def html_for_tags(tags)
    raise RuntimeError, 'No tags available' if tags.nil?
    res = ["<h1>Available tags</h1>", proj_info]
    res << '<ul>' << tags.reject {|t| t.nil? or t.empty?}.sort.map do |tag|
      '<li><a href="/github/%s/%s/%s.tar.gz">Download %s</a></li>' %
        [@author, @project, tag, tag]
    end << '</ul>'
    res << redir_description

    res.join("\n")
  end

  def error_msg_for(what)
    "<h1>Error opening project URL</h1>" + proj_info +
      "<p>#{what}</p>" + redir_description
  end

  def proj_info
    auth_link = '<a href="http://github.com/%s">%s</a>' % [@author, @author]
    proj_link = '<a href="http://github.com/%s/%s">%s</a>' % 
      [@author, @project, @project]
    "<p>Author: #{auth_link}<br/>Project: #{proj_link}</p>" 
  end

  def redir_description
    %q(<hr /><p>This redirctor is a tool written to ease the automated new 
       version downloading for automated QA in the Debian system.<br/>
       Anybody who finds this system useful can freely use it, although you 
       might be better served by the rich, official <a 
       href="http://github.com">GitHub.com</a> interface.<br/>
       For any questions regarding this script, please contact 
       <a href="mailto:gwolf@debian.org">Gunnar Wolf</a>.</p>)
  end
end

cgi = CGI.new
params = cgi.params
ghr = GitHubRedir.new(params['author'], params['project'], params['tag'])

cgi.out(ghr.http_headers) { ghr.result }
