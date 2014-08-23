/**
 * Created with PyCharm.
 * User: jan
 * Date: 19.09.12
 * Time: 05:01
 * To change this template use File | Settings | File Templates.
 */

function do_alert(message, fail) {
    var variables = {message:message, tag:"Info", type:"alert-success"};
    if (fail) {
        variables = {message:message, tag:"Error", type:"alert-error"};
    }
    var html = _.template($("#alert_template").html(), variables),
        placeholder = $("#alert_placeholder");
    placeholder.html(html);
    placeholder.find(">div").effect("highlight", {}, 600, null).delay(3500).fadeOut(500);
}

function set_checked(checked) {
    var ids = ["#video_lang", "#video_quality", "#submit_btn"];
    for (var i = 0; i < ids.length; i++) {
        if (checked) {
            $(ids[i]).removeAttr("disabled")
        } else {
            $(ids[i]).attr("disabled", "disabled")
        }
    }
}
set_checked(false);

function check_selection(selector, values) {
    $(selector).find(">option").each(function (idx, item) {
        var $item = $(item),
            value = $item.val();
        if (-1 < $.inArray(value, values)) {
            $item.removeAttr("disabled");
        } else {
            $item.attr("disabled", "disabled");
        }
    })
}


var Video = Backbone.Model.extend({
                                      defaults:{
                                          name:"No Name",
                                          url:"No Url",
                                          state:"NEW",
                                          progress:0
                                      },
                                      urlRoot:video_delete_url,
                                      initialize:function () {
                                          _.bindAll(this, "refresh", "check_state");
                                          this.check_state();
                                      },
                                      check_state:function () {
                                          if (this.get("state") != "COMPLETE") {
                                              window.setTimeout(this.refresh, 1000);
                                          }
                                      },
                                      refresh:function () {
                                          var self = this;
                                          $.post(video_info_url, {video_id:this.get("id")},function (resp) {
                                              if (resp.status == "OK") {
                                                  self.set(resp.data.video);
                                                  self.set({progress:resp.data.progress});
                                              }
                                              self.check_state();
                                          }, "json").error(function () {
                                                               self.check_state();
                                                           });
                                      }
                                  });

var VideoList = Backbone.Collection.extend({
                                               model:Video,
                                               url:videos_url
                                           });

var VideoView = Backbone.View.extend({
                                         tagName:'li',
                                         className:'span4',
                                         initialize:function () {
                                             _.bindAll(this, "render", "updateProgress", "stateChanged", "remove", "unrender");

                                             this.model.bind("change:progress", this.updateProgress);
                                             this.model.bind("change:state", this.stateChanged);
                                             this.model.bind('remove', this.unrender);
                                         },
                                         events:{
                                             "click span.video_delete":"remove"
                                         },
                                         remove:function (e) {
                                             this.model.destroy();
                                         },
                                         unrender:function () {
                                             $(this.el).remove();
                                         },
                                         render:function () {
                                             var data = this.model.toJSON();
                                             data.download = video_download_base + data.id + ".mp4";
                                             var html = _.template($("#video_template").html(), data);
                                             $(this.el).html(html);
                                             return this;
                                         },
                                         stateChanged:function () {
                                             if (this.model.get("state") == "COMPLETE" || this.model.get("state") == "CONVERTING" || this.model.get("state") == "LOADING") {
                                                 this.render();
                                             }
                                         },
                                         updateProgress:function () {
                                             var progress = this.model.get("progress"),
                                                 state = this.model.get("state");
                                             if (progress < 100 && state != "COMPLETE" && state != "CONVERING") {
                                                 $(this.el).find(".bar").css("width", progress + "%");
                                             }
                                         }
                                     });

var VideoListView = Backbone.View.extend({
                                             initialize:function () {
                                                 _.bindAll(this, "appendItem", "render");

                                                 this.collection = new VideoList();
                                                 this.collection.bind("add", this.appendItem);

                                                 var self = this;
                                                 this.collection.fetch({success:function () {
                                                     self.render();
                                                 }});

                                             },

                                             render:function () {
                                                 var self = this;
                                                 _(this.collection.models).each(function (item) {
                                                     self.appendItem(item);
                                                 })
                                             },
                                             appendItem:function (item) {
                                                 var view = new VideoView({
                                                                              model:item
                                                                          });
                                                 $(this.el).prepend(view.render().el)
                                             }
                                         });

var videoList = new VideoListView({el:$('#video_list')});

$("#video_url").on("keyup", function (e) {
    var video_url = $("#video_url").val();
    if (video_url == url) {
        return;
    }
    url = video_url;
    $.post(lookup_url, {video_url:video_url}, function (resp) {
        if (resp.status == "OK") {
            check_selection("#video_lang", resp.data.languages);
            check_selection("#video_quality", resp.data.qualities);
            set_checked(true)
        } else {
            set_checked(false)
        }
    }, "json")
});

$("#video_form").on("submit", function (e) {
    e.preventDefault();
    var video_url = $("#video_url").val(),
        video_lang = $("#video_lang").val(),
        video_quality = $("#video_quality").val(),
        data = {video_url:video_url, video_lang:video_lang, video_quality:video_quality};
    $.post(enqueu_url, data, function (resp) {
        if (resp.status != "OK") {
            do_alert(resp.data.message, true);
            return;
        }
        var videoItem = new Video();
        videoItem.set(resp.data.video);
        videoList.collection.add(videoItem);
    }, "json")
});

$("#video_form").on("reset", function (e) {
    set_checked(false);
    url = "";
});
