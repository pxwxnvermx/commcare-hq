hqDefine("cloudcare/js/formplayer/sessions/controller", function () {
    var constants = hqImport("cloudcare/js/formplayer/constants"),
        FormplayerFrontend = hqImport("cloudcare/js/formplayer/app"),
        Views = hqImport("cloudcare/js/formplayer/sessions/views");

    return {
        listSessions: function listSessions(pageNumber, pageSize) {
            /* eslint-disable */
            if (pageSize == null) {
                pageSize = constants.DEFAULT_INCOMPLETE_FORMS_PAGE_SIZE;
            }
            /* eslint-disable */
            if (pageNumber == null) {
                pageNumber = 0;
            }
            var fetchingSessions = FormplayerFrontend.getChannel().request("sessions", pageNumber, pageSize);

            $.when(fetchingSessions).done(function (sessions) {

                var sessionListView = Views({
                    collection: sessions,
                });

                FormplayerFrontend.regions.getRegion('main').show(sessionListView);
                var totalPages = Math.max(1, Math.ceil(sessions.totalSessions / pageSize));
                if (totalPages > 1) {
                    $('#sessions-paginator').bootpag({
                        page: pageNumber + 1,
                        total: totalPages,
                        maxVisible: Math.min(totalPages, 5),
                        firstLastUse: true,
                    }).on("page", function (event, page) {
                        listSessions(page - 1, pageSize);
                    });
                }
            });
        },
    };
});
