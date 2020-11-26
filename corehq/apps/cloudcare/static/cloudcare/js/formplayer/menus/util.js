/*global Backbone */

hqDefine("cloudcare/js/formplayer/menus/util", function () {
    var FormplayerFrontend = hqImport("cloudcare/js/formplayer/app");

    var recordPosition = function (position) {
        sessionStorage.locationLat = position.coords.latitude;
        sessionStorage.locationLon = position.coords.longitude;
        sessionStorage.locationAltitude = position.coords.altitude;
        sessionStorage.locationAccuracy = position.coords.accuracy;
    };

    var handleLocationRequest = function (optionsFromLastRequest) {
        var success = function (position) {
            FormplayerFrontend.regions.getRegion('loadingProgress').empty();
            recordPosition(position);
            hqImport("cloudcare/js/formplayer/menus/controller").selectMenu(optionsFromLastRequest);
        };

        var error = function (err) {
            FormplayerFrontend.regions.getRegion('loadingProgress').empty();
            FormplayerFrontend.trigger('showError',
                getErrorMessage(err) +
                "Without access to your location, computations that rely on the here() function will show up blank.");
        };

        var getErrorMessage = function (err) {
            switch (err.code) {
                case err.PERMISSION_DENIED:
                    return "You denied CommCare HQ permission to read your browser's current location. ";
                case err.TIMEOUT:
                    return "Your connection was not strong enough to acquire your location. Please try again later. ";
                case err.POSITION_UNAVAILABLE:
                default:
                    return "Your browser location could not be determined. ";
            }
        };

        if (navigator.geolocation) {
            var progressView = hqImport("cloudcare/js/formplayer/layout/views/progress_bar")({
                progressMessage: "Fetching your location...",
            });
            FormplayerFrontend.regions.getRegion('loadingProgress').show(progressView.render());
            navigator.geolocation.getCurrentPosition(success, error, {timeout: 10000});
        }
    };

    var startOrStopLocationWatching = function (shouldWatchLocation) {
        if (navigator.geolocation) {
            var watching = Boolean(sessionStorage.lastLocationWatchId);
            if (!watching && shouldWatchLocation) {
                sessionStorage.lastLocationWatchId = navigator.geolocation.watchPosition(recordPosition);
            } else if (watching && !shouldWatchLocation) {
                navigator.geolocation.clearWatch(sessionStorage.lastLocationWatchId);
                sessionStorage.lastLocationWatchId = '';
            }
        }
    };

    var showBreadcrumbs = function (breadcrumbs) {
        var detailCollection,
            breadcrumbModels;

        breadcrumbModels = _.map(breadcrumbs, function (breadcrumb, idx) {
            return {
                data: breadcrumb,
                id: idx,
            };
        });

        detailCollection = new Backbone.Collection(breadcrumbModels);
        var breadcrumbView = hqImport("cloudcare/js/formplayer/menus/views").BreadcrumbListView({
            collection: detailCollection,
        });
        FormplayerFrontend.regions.getRegion('breadcrumb').show(breadcrumbView);
    };

    var showLanguageMenu = function (langs) {
        var langModels,
            langCollection;

        FormplayerFrontend.regions.addRegions({
            formMenu: "#form-menu",
        });
        langModels = _.map(langs, function (lang) {
            return {
                lang: lang,
            };
        });

        langCollection = new Backbone.Collection(langModels);
        var formMenuView = hqImport("cloudcare/js/formplayer/menus/views").FormMenuView({
            collection: langCollection,
        });
        FormplayerFrontend.regions.getRegion('formMenu').show(formMenuView);
    };


    var getMenuView = function (menuResponse) {
        var menuData = {
            collection: menuResponse,
            title: menuResponse.title,
            headers: menuResponse.headers,
            widthHints: menuResponse.widthHints,
            actions: menuResponse.actions,
            pageCount: menuResponse.pageCount,
            currentPage: menuResponse.currentPage,
            styles: menuResponse.styles,
            type: menuResponse.type,
            sessionId: menuResponse.sessionId,
            tiles: menuResponse.tiles,
            numEntitiesPerRow: menuResponse.numEntitiesPerRow,
            maxHeight: menuResponse.maxHeight,
            maxWidth: menuResponse.maxWidth,
            useUniformUnits: menuResponse.useUniformUnits,
            isPersistentDetail: menuResponse.isPersistentDetail,
            sortIndices: menuResponse.sortIndices,
        };
        if (menuResponse.breadcrumbs.length === 2 && hqImport('hqwebapp/js/toggles').toggleEnabled('APP_ANALYTICS')) {
            hqImport('analytix/js/kissmetrix').track.event('Viewed Case List', {
                domain: FormplayerFrontend.getChannel().request("currentUser").domain,
                app_id: FormplayerFrontend.getChannel().request('getCurrentAppId'),
                name: menuResponse.breadcrumbs[1],
            });
        }
        if (menuResponse.type === "commands") {
            return hqImport("cloudcare/js/formplayer/menus/views").MenuListView(menuData);
        } else if (menuResponse.type === "query") {
            return hqImport("cloudcare/js/formplayer/menus/views/query")(menuData);
        } else if (menuResponse.type === "entities") {
            if (menuResponse.tiles === null || menuResponse.tiles === undefined) {
                return hqImport("cloudcare/js/formplayer/menus/views").CaseListView(menuData);
            } else {
                if (menuResponse.numEntitiesPerRow > 1) {
                    return hqImport("cloudcare/js/formplayer/menus/views").GridCaseTileListView(menuData);
                } else {
                    return hqImport("cloudcare/js/formplayer/menus/views").CaseTileListView(menuData);
                }
            }
        }
    };

    return {
        getMenuView: getMenuView,
        handleLocationRequest: handleLocationRequest,
        showBreadcrumbs: showBreadcrumbs,
        showLanguageMenu: showLanguageMenu,
        startOrStopLocationWatching: startOrStopLocationWatching,
    };
});
