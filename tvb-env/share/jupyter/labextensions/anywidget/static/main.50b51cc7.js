(() => { // webpackBootstrap
"use strict";
var __webpack_modules__ = ({
702: (function () {

;// CONCATENATED MODULE: ./node_modules/.pnpm/@lukeed+uuid@2.0.1/node_modules/@lukeed/uuid/dist/index.mjs
var IDX=256, HEX=[], BUFFER;
while (IDX--) HEX[IDX] = (IDX + 256).toString(16).substring(1);

function v4() {
	var i=0, num, out='';

	if (!BUFFER || ((IDX + 16) > 256)) {
		BUFFER = Array(i=256);
		while (i--) BUFFER[i] = 256 * Math.random() | 0;
		i = IDX = 0;
	}

	for (; i < 16; i++) {
		num = BUFFER[IDX + i];
		if (i==6) out += HEX[num & 15 | 64];
		else if (i==8) out += HEX[num & 63 | 128];
		else out += HEX[num];

		if (i & 1 && i > 1 && i < 11) out += '-';
	}

	IDX++;
	return out;
}

;// CONCATENATED MODULE: ./packages/anywidget/src/widget.js



/** @import * as base from "@jupyter-widgets/base" */
/** @import { Initialize, Render, AnyModel } from "@anywidget/types" */

/**
 * @template T
 * @typedef {T | PromiseLike<T>} Awaitable
 */

/**
 * @typedef AnyWidget
 * @prop initialize {Initialize}
 * @prop render {Render}
 */

/**
 *  @typedef AnyWidgetModule
 *  @prop render {Render=}
 *  @prop default {AnyWidget | (() => AnyWidget | Promise<AnyWidget>)=}
 */

/**
 * @param {unknown} condition
 * @param {string} message
 * @returns {asserts condition}
 */
function assert(condition, message) {
	if (!condition) throw new Error(message);
}

/**
 * @param {string} str
 * @returns {str is "https://${string}" | "http://${string}"}
 */
function is_href(str) {
	return str.startsWith("http://") || str.startsWith("https://");
}

/**
 * @param {string} href
 * @param {string} anywidget_id
 * @returns {Promise<void>}
 */
async function load_css_href(href, anywidget_id) {
	/** @type {HTMLLinkElement | null} */
	let prev = document.querySelector(`link[id='${anywidget_id}']`);

	// Adapted from https://github.com/vitejs/vite/blob/d59e1acc2efc0307488364e9f2fad528ec57f204/packages/vite/src/client/client.ts#L185-L201
	// Swaps out old styles with new, but avoids flash of unstyled content.
	// No need to await the load since we already have styles applied.
	if (prev) {
		let newLink = /** @type {HTMLLinkElement} */ (prev.cloneNode());
		newLink.href = href;
		newLink.addEventListener("load", () => prev?.remove());
		newLink.addEventListener("error", () => prev?.remove());
		prev.after(newLink);
		return;
	}

	return new Promise((resolve) => {
		let link = Object.assign(document.createElement("link"), {
			rel: "stylesheet",
			href,
			onload: resolve,
		});
		document.head.appendChild(link);
	});
}

/**
 * @param {string} css_text
 * @param {string} anywidget_id
 * @returns {void}
 */
function load_css_text(css_text, anywidget_id) {
	/** @type {HTMLStyleElement | null} */
	let prev = document.querySelector(`style[id='${anywidget_id}']`);
	if (prev) {
		// replace instead of creating a new DOM node
		prev.textContent = css_text;
		return;
	}
	let style = Object.assign(document.createElement("style"), {
		id: anywidget_id,
		type: "text/css",
	});
	style.appendChild(document.createTextNode(css_text));
	document.head.appendChild(style);
}

/**
 * @param {string | undefined} css
 * @param {string} anywidget_id
 * @returns {Promise<void>}
 */
async function load_css(css, anywidget_id) {
	if (!css || !anywidget_id) return;
	if (is_href(css)) return load_css_href(css, anywidget_id);
	return load_css_text(css, anywidget_id);
}

/**
 * @param {string} esm
 * @returns {Promise<AnyWidgetModule>}
 */
async function load_esm(esm) {
	if (is_href(esm)) {
		return await import(/* webpackIgnore: true */ /* @vite-ignore */ esm);
	}
	let url = URL.createObjectURL(new Blob([esm], { type: "text/javascript" }));
	let mod = await import(/* webpackIgnore: true */ /* @vite-ignore */ url);
	URL.revokeObjectURL(url);
	return mod;
}

/** @param {string} anywidget_id */
function warn_render_deprecation(anywidget_id) {
	console.warn(`\
[anywidget] Deprecation Warning for ${anywidget_id}: Direct export of a 'render' will likely be deprecated in the future. To migrate ...

Remove the 'export' keyword from 'render'
-----------------------------------------

export function render({ model, el }) { ... }
^^^^^^

Create a default export that returns an object with 'render'
------------------------------------------------------------

function render({ model, el }) { ... }
         ^^^^^^
export default { render }
                 ^^^^^^

Pin to anywidget>=0.9.0 in your pyproject.toml
----------------------------------------------

dependencies = ["anywidget>=0.9.0"]

To learn more, please see: https://github.com/manzt/anywidget/pull/395.
`);
}

/**
 * @param {string} esm
 * @param {string} anywidget_id
 * @returns {Promise<AnyWidget>}
 */
async function load_widget(esm, anywidget_id) {
	let mod = await load_esm(esm);
	if (mod.render) {
		warn_render_deprecation(anywidget_id);
		return {
			async initialize() {},
			render: mod.render,
		};
	}
	assert(
		mod.default,
		`[anywidget] module must export a default function or object.`,
	);
	let widget =
		typeof mod.default === "function" ? await mod.default() : mod.default;
	return widget;
}

/**
 * This is a trick so that we can cleanup event listeners added
 * by the user-defined function.
 */
let INITIALIZE_MARKER = Symbol("anywidget.initialize");

/**
 * @param {base.DOMWidgetModel} model
 * @param {unknown} context
 * @return {import("@anywidget/types").AnyModel}
 *
 * Prunes the view down to the minimum context necessary.
 *
 * Calls to `model.get` and `model.set` automatically add the
 * `context`, so we can gracefully unsubscribe from events
 * added by user-defined hooks.
 */
function model_proxy(model, context) {
	return {
		get: model.get.bind(model),
		set: model.set.bind(model),
		save_changes: model.save_changes.bind(model),
		send: model.send.bind(model),
		// @ts-expect-error
		on(name, callback) {
			model.on(name, callback, context);
		},
		off(name, callback) {
			model.off(name, callback, context);
		},
		// @ts-expect-error - the widget_manager type is wider than what
		// we want to expose to developers.
		// In a future version, we will expose a more limited API but
		// that can wait for a minor version bump.
		widget_manager: model.widget_manager,
	};
}

/**
 * @param {void | (() => Awaitable<void>)} fn
 * @param {string} kind
 */
async function safe_cleanup(fn, kind) {
	return Promise.resolve()
		.then(() => fn?.())
		.catch((e) => console.warn(`[anywidget] error cleaning up ${kind}.`, e));
}

/**
 * @template T
 * @typedef Ready
 * @property {"ready"} status
 * @property {T} data
 */

/**
 * @typedef Pending
 * @property {"pending"} status
 */

/**
 * @typedef Errored
 * @property {"error"} status
 * @property {unknown} error
 */

/**
 * @template T
 * @typedef {Pending | Ready<T> | Errored} Result
 */

/**
 * Cleans up the stack trace at anywidget boundary.
 * You can fully inspect the entire stack trace in the console interactively,
 * but the initial error message is cleaned up to be more user-friendly.
 *
 * @param {unknown} source
 */
function throw_anywidget_error(source) {
	if (!(source instanceof Error)) {
		// Don't know what to do with this.
		throw source;
	}
	let lines = source.stack?.split("\n") ?? [];
	let anywidget_index = lines.findIndex((line) => line.includes("anywidget"));
	let clean_stack =
		anywidget_index === -1 ? lines : lines.slice(0, anywidget_index + 1);
	source.stack = clean_stack.join("\n");
	console.error(source);
	throw source;
}

/**
 * @typedef InvokeOptions
 * @prop {DataView[]} [buffers]
 * @prop {AbortSignal} [signal]
 */

/**
 * @template T
 * @param {import("@anywidget/types").AnyModel} model
 * @param {string} name
 * @param {any} [msg]
 * @param {InvokeOptions} [options]
 * @return {Promise<[T, DataView[]]>}
 */
function invoke(model, name, msg, options = {}) {
	// crypto.randomUUID() is not available in non-secure contexts (i.e., http://)
	// so we use simple (non-secure) polyfill.
	let id = uuid.v4();
	let signal = options.signal ?? AbortSignal.timeout(3000);

	return new Promise((resolve, reject) => {
		if (signal.aborted) {
			reject(signal.reason);
		}
		signal.addEventListener("abort", () => {
			model.off("msg:custom", handler);
			reject(signal.reason);
		});

		/**
		 * @param {{ id: string, kind: "anywidget-command-response", response: T }} msg
		 * @param {DataView[]} buffers
		 */
		function handler(msg, buffers) {
			if (!(msg.id === id)) return;
			resolve([msg.response, buffers]);
			model.off("msg:custom", handler);
		}
		model.on("msg:custom", handler);
		model.send(
			{ id, kind: "anywidget-command", name, msg },
			undefined,
			options.buffers ?? [],
		);
	});
}

/**
 * Polyfill for {@link https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/withResolvers Promise.withResolvers}
 *
 * Trevor(2025-03-14): Should be able to remove once more stable across browsers.
 *
 * @template T
 * @returns {PromiseWithResolvers<T>}
 */
function promise_with_resolvers() {
	let resolve;
	let reject;
	let promise = new Promise((res, rej) => {
		resolve = res;
		reject = rej;
	});
	// @ts-expect-error - We know these types are ok
	return { promise, resolve, reject };
}

/**
 * @template {Record<string, unknown>} T
 * @template {keyof T & string} K
 * @param {AnyModel<T>} model
 * @param {K} name
 * @param {{ signal?: AbortSignal}} options
 * @returns {solid.Accessor<T[K]>}
 */
function observe(model, name, { signal }) {
	let [get, set] = solid.createSignal(model.get(name));
	let update = () => set(() => model.get(name));
	model.on(`change:${name}`, update);
	signal?.addEventListener("abort", () => {
		model.off(`change:${name}`, update);
	});
	return get;
}

/**
 * @typedef State
 * @property {string} _esm
 * @property {string} _anywidget_id
 * @property {string | undefined} _css
 */

class Runtime {
	/** @type {solid.Accessor<Result<AnyWidget>>} */
	// @ts-expect-error - Set synchronously in constructor.
	#widget_result;
	/** @type {AbortSignal} */
	#signal;
	/** @type {Promise<void>} */
	ready;

	/**
	 * @param {base.DOMWidgetModel} model
	 * @param {{ signal: AbortSignal }} options
	 */
	constructor(model, options) {
		/** @type {PromiseWithResolvers<void>} */
		let resolvers = promise_with_resolvers();
		this.ready = resolvers.promise;
		this.#signal = options.signal;
		this.#signal.throwIfAborted();
		this.#signal.addEventListener("abort", () => dispose());
		AbortSignal.timeout(2000).addEventListener("abort", () => {
			resolvers.reject(new Error("[anywidget] Failed to initialize model."));
		});
		let dispose = solid.createRoot((dispose) => {
			/** @type {AnyModel<State>} */
			// @ts-expect-error - Types don't sufficiently overlap, so we cast here for type-safe access
			let typed_model = model;
			let id = typed_model.get("_anywidget_id");
			let css = observe(typed_model, "_css", { signal: this.#signal });
			let esm = observe(typed_model, "_esm", { signal: this.#signal });
			let [widget_result, set_widget_result] = solid.createSignal(
				/** @type {Result<AnyWidget>} */ ({ status: "pending" }),
			);
			this.#widget_result = widget_result;

			solid.createEffect(
				solid.on(
					css,
					() => console.debug(`[anywidget] css hot updated: ${id}`),
					{ defer: true },
				),
			);
			solid.createEffect(
				solid.on(
					esm,
					() => console.debug(`[anywidget] esm hot updated: ${id}`),
					{ defer: true },
				),
			);
			solid.createEffect(() => {
				load_css(css(), id);
			});
			solid.createEffect(() => {
				let controller = new AbortController();
				solid.onCleanup(() => controller.abort());
				model.off(null, null, INITIALIZE_MARKER);
				load_widget(esm(), id)
					.then(async (widget) => {
						if (controller.signal.aborted) {
							return;
						}
						let cleanup = await widget.initialize?.({
							model: model_proxy(model, INITIALIZE_MARKER),
							experimental: {
								// @ts-expect-error - bind isn't working
								invoke: invoke.bind(null, model),
							},
						});
						if (controller.signal.aborted) {
							safe_cleanup(cleanup, "esm update");
							return;
						}
						controller.signal.addEventListener("abort", () =>
							safe_cleanup(cleanup, "esm update"),
						);
						set_widget_result({ status: "ready", data: widget });
						resolvers.resolve();
					})
					.catch((error) => set_widget_result({ status: "error", error }));
			});

			return dispose;
		});
	}

	/**
	 * @param {base.DOMWidgetView} view
	 * @param {{ signal: AbortSignal }} options
	 * @returns {Promise<void>}
	 */
	async create_view(view, options) {
		let model = view.model;
		let signal = AbortSignal.any([this.#signal, options.signal]); // either model or view destroyed
		signal.throwIfAborted();
		signal.addEventListener("abort", () => dispose());
		let dispose = solid.createRoot((dispose) => {
			solid.createEffect(() => {
				// Clear all previous event listeners from this hook.
				model.off(null, null, view);
				view.$el.empty();
				let result = this.#widget_result();
				if (result.status === "pending") {
					return;
				}
				if (result.status === "error") {
					throw_anywidget_error(result.error);
					return;
				}
				let controller = new AbortController();
				solid.onCleanup(() => controller.abort());
				Promise.resolve()
					.then(async () => {
						let cleanup = await result.data.render?.({
							model: model_proxy(model, view),
							el: view.el,
							experimental: {
								// @ts-expect-error - bind isn't working
								invoke: invoke.bind(null, model),
							},
						});
						if (controller.signal.aborted) {
							safe_cleanup(cleanup, "dispose view - already aborted");
							return;
						}
						controller.signal.addEventListener("abort", () =>
							safe_cleanup(cleanup, "dispose view - aborted"),
						);
					})
					.catch((error) => throw_anywidget_error(error));
			});
			return () => dispose();
		});
	}
}

// @ts-expect-error - injected by bundler
let version = "0.9.21";

/**
 * @param {base} options
 * @returns {{ AnyModel: typeof base.DOMWidgetModel, AnyView: typeof base.DOMWidgetView }}
 */
/* ESM default export */ function src_widget({ DOMWidgetModel, DOMWidgetView }) {
	/** @type {WeakMap<AnyModel, Runtime>} */
	let RUNTIMES = new WeakMap();

	class AnyModel extends DOMWidgetModel {
		static model_name = "AnyModel";
		static model_module = "anywidget";
		static model_module_version = version;

		static view_name = "AnyView";
		static view_module = "anywidget";
		static view_module_version = version;

		/** @param {Parameters<InstanceType<DOMWidgetModel>["initialize"]>} args */
		initialize(...args) {
			super.initialize(...args);
			let controller = new AbortController();
			this.once("destroy", () => {
				controller.abort("[anywidget] Runtime destroyed.");
				RUNTIMES.delete(this);
			});
			RUNTIMES.set(this, new Runtime(this, { signal: controller.signal }));
		}

		/** @param {Parameters<InstanceType<DOMWidgetModel>["_handle_comm_msg"]>} msg */
		async _handle_comm_msg(...msg) {
			let runtime = RUNTIMES.get(this);
			await runtime?.ready;
			return super._handle_comm_msg(...msg);
		}

		/**
		 * @param {Record<string, any>} state
		 *
		 * We override to support binary trailets because JSON.parse(JSON.stringify())
		 * does not properly clone binary data (it just returns an empty object).
		 *
		 * https://github.com/jupyter-widgets/ipywidgets/blob/47058a373d2c2b3acf101677b2745e14b76dd74b/packages/base/src/widget.ts#L562-L583
		 */
		serialize(state) {
			let serializers =
				/** @type {DOMWidgetModel} */ (this.constructor).serializers || {};
			for (let k of Object.keys(state)) {
				try {
					let serialize = serializers[k]?.serialize;
					if (serialize) {
						state[k] = serialize(state[k], this);
					} else if (k === "layout" || k === "style") {
						// These keys come from ipywidgets, rely on JSON.stringify trick.
						state[k] = JSON.parse(JSON.stringify(state[k]));
					} else {
						state[k] = structuredClone(state[k]);
					}
					if (typeof state[k]?.toJSON === "function") {
						state[k] = state[k].toJSON();
					}
				} catch (e) {
					console.error("Error serializing widget state attribute: ", k);
					throw e;
				}
			}
			return state;
		}
	}

	class AnyView extends DOMWidgetView {
		#controller = new AbortController();
		async render() {
			let runtime = RUNTIMES.get(this.model);
			assert(runtime, "[anywidget] Runtime not found.");
			await runtime.create_view(this, { signal: this.#controller.signal });
		}
		remove() {
			this.#controller.abort("[anywidget] View destroyed.");
			super.remove();
		}
	}

	return { AnyModel, AnyView };
}

;// CONCATENATED MODULE: ./packages/anywidget/src/index.js


// @ts-expect-error -- define is a global provided by the notebook runtime.
define(["@jupyter-widgets/base"], create);


}),

});
/************************************************************************/
// The module cache
var __webpack_module_cache__ = {};

// The require function
function __webpack_require__(moduleId) {

// Check if module is in cache
var cachedModule = __webpack_module_cache__[moduleId];
if (cachedModule !== undefined) {
return cachedModule.exports;
}
// Create a new module (and put it into the cache)
var module = (__webpack_module_cache__[moduleId] = {
exports: {}
});
// Execute the module function
__webpack_modules__[moduleId](module, module.exports, __webpack_require__);

// Return the exports of the module
return module.exports;

}

// expose the modules object (__webpack_modules__)
__webpack_require__.m = __webpack_modules__;

// expose the module cache
__webpack_require__.c = __webpack_module_cache__;

/************************************************************************/
// webpack/runtime/has_own_property
(() => {
__webpack_require__.o = (obj, prop) => (Object.prototype.hasOwnProperty.call(obj, prop))
})();
// webpack/runtime/rspack_version
(() => {
__webpack_require__.rv = () => ("1.5.8")
})();
// webpack/runtime/sharing
(() => {

__webpack_require__.S = {};
__webpack_require__.initializeSharingData = { scopeToSharingDataMapping: {  }, uniqueName: "@anywidget/monorepo" };
var initPromises = {};
var initTokens = {};
__webpack_require__.I = function(name, initScope) {
	if (!initScope) initScope = [];
	// handling circular init calls
	var initToken = initTokens[name];
	if (!initToken) initToken = initTokens[name] = {};
	if (initScope.indexOf(initToken) >= 0) return;
	initScope.push(initToken);
	// only runs once
	if (initPromises[name]) return initPromises[name];
	// creates a new share scope if needed
	if (!__webpack_require__.o(__webpack_require__.S, name))
		__webpack_require__.S[name] = {};
	// runs all init snippets from all modules reachable
	var scope = __webpack_require__.S[name];
	var warn = function (msg) {
		if (typeof console !== "undefined" && console.warn) console.warn(msg);
	};
	var uniqueName = __webpack_require__.initializeSharingData.uniqueName;
	var register = function (name, version, factory, eager) {
		var versions = (scope[name] = scope[name] || {});
		var activeVersion = versions[version];
		if (
			!activeVersion ||
			(!activeVersion.loaded &&
				(!eager != !activeVersion.eager
					? eager
					: uniqueName > activeVersion.from))
		)
			versions[version] = { get: factory, from: uniqueName, eager: !!eager };
	};
	var initExternal = function (id) {
		var handleError = function (err) {
			warn("Initialization of sharing external failed: " + err);
		};
		try {
			var module = __webpack_require__(id);
			if (!module) return;
			var initFn = function (module) {
				return (
					module &&
					module.init &&
					module.init(__webpack_require__.S[name], initScope)
				);
			};
			if (module.then) return promises.push(module.then(initFn, handleError));
			var initResult = initFn(module);
			if (initResult && initResult.then)
				return promises.push(initResult["catch"](handleError));
		} catch (err) {
			handleError(err);
		}
	};
	var promises = [];
	var scopeToSharingDataMapping = __webpack_require__.initializeSharingData.scopeToSharingDataMapping;
	if (scopeToSharingDataMapping[name]) {
		scopeToSharingDataMapping[name].forEach(function (stage) {
			if (typeof stage === "object") register(stage.name, stage.version, stage.factory, stage.eager);
			else initExternal(stage)
		});
	}
	if (!promises.length) return (initPromises[name] = 1);
	return (initPromises[name] = Promise.all(promises).then(function () {
		return (initPromises[name] = 1);
	}));
};


})();
// webpack/runtime/rspack_unique_id
(() => {
__webpack_require__.ruid = "bundler=rspack@1.5.8";

})();
/************************************************************************/
// module cache are used so entry inlining is disabled
// startup
// Load entry module and return exports
var __webpack_exports__ = __webpack_require__(702);
})()
;
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoibWFpbi43MGY0NmQ3Ni5qcyIsInNvdXJjZXMiOlsid2VicGFjazovL0Bhbnl3aWRnZXQvbW9ub3JlcG8vLi9ub2RlX21vZHVsZXMvLnBucG0vQGx1a2VlZCt1dWlkQDIuMC4xL25vZGVfbW9kdWxlcy9AbHVrZWVkL3V1aWQvZGlzdC9pbmRleC5tanMiLCJ3ZWJwYWNrOi8vQGFueXdpZGdldC9tb25vcmVwby8uL3BhY2thZ2VzL2FueXdpZGdldC9zcmMvd2lkZ2V0LmpzIiwid2VicGFjazovL0Bhbnl3aWRnZXQvbW9ub3JlcG8vLi9wYWNrYWdlcy9hbnl3aWRnZXQvc3JjL2luZGV4LmpzIiwid2VicGFjazovL0Bhbnl3aWRnZXQvbW9ub3JlcG8vd2VicGFjay9ydW50aW1lL2hhc19vd25fcHJvcGVydHkiLCJ3ZWJwYWNrOi8vQGFueXdpZGdldC9tb25vcmVwby93ZWJwYWNrL3J1bnRpbWUvcnNwYWNrX3ZlcnNpb24iLCJ3ZWJwYWNrOi8vQGFueXdpZGdldC9tb25vcmVwby93ZWJwYWNrL3J1bnRpbWUvc2hhcmluZyIsIndlYnBhY2s6Ly9AYW55d2lkZ2V0L21vbm9yZXBvL3dlYnBhY2svcnVudGltZS9yc3BhY2tfdW5pcXVlX2lkIl0sInNvdXJjZXNDb250ZW50IjpbInZhciBJRFg9MjU2LCBIRVg9W10sIEJVRkZFUjtcbndoaWxlIChJRFgtLSkgSEVYW0lEWF0gPSAoSURYICsgMjU2KS50b1N0cmluZygxNikuc3Vic3RyaW5nKDEpO1xuXG5leHBvcnQgZnVuY3Rpb24gdjQoKSB7XG5cdHZhciBpPTAsIG51bSwgb3V0PScnO1xuXG5cdGlmICghQlVGRkVSIHx8ICgoSURYICsgMTYpID4gMjU2KSkge1xuXHRcdEJVRkZFUiA9IEFycmF5KGk9MjU2KTtcblx0XHR3aGlsZSAoaS0tKSBCVUZGRVJbaV0gPSAyNTYgKiBNYXRoLnJhbmRvbSgpIHwgMDtcblx0XHRpID0gSURYID0gMDtcblx0fVxuXG5cdGZvciAoOyBpIDwgMTY7IGkrKykge1xuXHRcdG51bSA9IEJVRkZFUltJRFggKyBpXTtcblx0XHRpZiAoaT09Nikgb3V0ICs9IEhFWFtudW0gJiAxNSB8IDY0XTtcblx0XHRlbHNlIGlmIChpPT04KSBvdXQgKz0gSEVYW251bSAmIDYzIHwgMTI4XTtcblx0XHRlbHNlIG91dCArPSBIRVhbbnVtXTtcblxuXHRcdGlmIChpICYgMSAmJiBpID4gMSAmJiBpIDwgMTEpIG91dCArPSAnLSc7XG5cdH1cblxuXHRJRFgrKztcblx0cmV0dXJuIG91dDtcbn1cbiIsImltcG9ydCAqIGFzIHV1aWQgZnJvbSBcIkBsdWtlZWQvdXVpZFwiO1xuaW1wb3J0ICogYXMgc29saWQgZnJvbSBcInNvbGlkLWpzXCI7XG5cbi8qKiBAaW1wb3J0ICogYXMgYmFzZSBmcm9tIFwiQGp1cHl0ZXItd2lkZ2V0cy9iYXNlXCIgKi9cbi8qKiBAaW1wb3J0IHsgSW5pdGlhbGl6ZSwgUmVuZGVyLCBBbnlNb2RlbCB9IGZyb20gXCJAYW55d2lkZ2V0L3R5cGVzXCIgKi9cblxuLyoqXG4gKiBAdGVtcGxhdGUgVFxuICogQHR5cGVkZWYge1QgfCBQcm9taXNlTGlrZTxUPn0gQXdhaXRhYmxlXG4gKi9cblxuLyoqXG4gKiBAdHlwZWRlZiBBbnlXaWRnZXRcbiAqIEBwcm9wIGluaXRpYWxpemUge0luaXRpYWxpemV9XG4gKiBAcHJvcCByZW5kZXIge1JlbmRlcn1cbiAqL1xuXG4vKipcbiAqICBAdHlwZWRlZiBBbnlXaWRnZXRNb2R1bGVcbiAqICBAcHJvcCByZW5kZXIge1JlbmRlcj19XG4gKiAgQHByb3AgZGVmYXVsdCB7QW55V2lkZ2V0IHwgKCgpID0+IEFueVdpZGdldCB8IFByb21pc2U8QW55V2lkZ2V0Pik9fVxuICovXG5cbi8qKlxuICogQHBhcmFtIHt1bmtub3dufSBjb25kaXRpb25cbiAqIEBwYXJhbSB7c3RyaW5nfSBtZXNzYWdlXG4gKiBAcmV0dXJucyB7YXNzZXJ0cyBjb25kaXRpb259XG4gKi9cbmZ1bmN0aW9uIGFzc2VydChjb25kaXRpb24sIG1lc3NhZ2UpIHtcblx0aWYgKCFjb25kaXRpb24pIHRocm93IG5ldyBFcnJvcihtZXNzYWdlKTtcbn1cblxuLyoqXG4gKiBAcGFyYW0ge3N0cmluZ30gc3RyXG4gKiBAcmV0dXJucyB7c3RyIGlzIFwiaHR0cHM6Ly8ke3N0cmluZ31cIiB8IFwiaHR0cDovLyR7c3RyaW5nfVwifVxuICovXG5mdW5jdGlvbiBpc19ocmVmKHN0cikge1xuXHRyZXR1cm4gc3RyLnN0YXJ0c1dpdGgoXCJodHRwOi8vXCIpIHx8IHN0ci5zdGFydHNXaXRoKFwiaHR0cHM6Ly9cIik7XG59XG5cbi8qKlxuICogQHBhcmFtIHtzdHJpbmd9IGhyZWZcbiAqIEBwYXJhbSB7c3RyaW5nfSBhbnl3aWRnZXRfaWRcbiAqIEByZXR1cm5zIHtQcm9taXNlPHZvaWQ+fVxuICovXG5hc3luYyBmdW5jdGlvbiBsb2FkX2Nzc19ocmVmKGhyZWYsIGFueXdpZGdldF9pZCkge1xuXHQvKiogQHR5cGUge0hUTUxMaW5rRWxlbWVudCB8IG51bGx9ICovXG5cdGxldCBwcmV2ID0gZG9jdW1lbnQucXVlcnlTZWxlY3RvcihgbGlua1tpZD0nJHthbnl3aWRnZXRfaWR9J11gKTtcblxuXHQvLyBBZGFwdGVkIGZyb20gaHR0cHM6Ly9naXRodWIuY29tL3ZpdGVqcy92aXRlL2Jsb2IvZDU5ZTFhY2MyZWZjMDMwNzQ4ODM2NGU5ZjJmYWQ1MjhlYzU3ZjIwNC9wYWNrYWdlcy92aXRlL3NyYy9jbGllbnQvY2xpZW50LnRzI0wxODUtTDIwMVxuXHQvLyBTd2FwcyBvdXQgb2xkIHN0eWxlcyB3aXRoIG5ldywgYnV0IGF2b2lkcyBmbGFzaCBvZiB1bnN0eWxlZCBjb250ZW50LlxuXHQvLyBObyBuZWVkIHRvIGF3YWl0IHRoZSBsb2FkIHNpbmNlIHdlIGFscmVhZHkgaGF2ZSBzdHlsZXMgYXBwbGllZC5cblx0aWYgKHByZXYpIHtcblx0XHRsZXQgbmV3TGluayA9IC8qKiBAdHlwZSB7SFRNTExpbmtFbGVtZW50fSAqLyAocHJldi5jbG9uZU5vZGUoKSk7XG5cdFx0bmV3TGluay5ocmVmID0gaHJlZjtcblx0XHRuZXdMaW5rLmFkZEV2ZW50TGlzdGVuZXIoXCJsb2FkXCIsICgpID0+IHByZXY/LnJlbW92ZSgpKTtcblx0XHRuZXdMaW5rLmFkZEV2ZW50TGlzdGVuZXIoXCJlcnJvclwiLCAoKSA9PiBwcmV2Py5yZW1vdmUoKSk7XG5cdFx0cHJldi5hZnRlcihuZXdMaW5rKTtcblx0XHRyZXR1cm47XG5cdH1cblxuXHRyZXR1cm4gbmV3IFByb21pc2UoKHJlc29sdmUpID0+IHtcblx0XHRsZXQgbGluayA9IE9iamVjdC5hc3NpZ24oZG9jdW1lbnQuY3JlYXRlRWxlbWVudChcImxpbmtcIiksIHtcblx0XHRcdHJlbDogXCJzdHlsZXNoZWV0XCIsXG5cdFx0XHRocmVmLFxuXHRcdFx0b25sb2FkOiByZXNvbHZlLFxuXHRcdH0pO1xuXHRcdGRvY3VtZW50LmhlYWQuYXBwZW5kQ2hpbGQobGluayk7XG5cdH0pO1xufVxuXG4vKipcbiAqIEBwYXJhbSB7c3RyaW5nfSBjc3NfdGV4dFxuICogQHBhcmFtIHtzdHJpbmd9IGFueXdpZGdldF9pZFxuICogQHJldHVybnMge3ZvaWR9XG4gKi9cbmZ1bmN0aW9uIGxvYWRfY3NzX3RleHQoY3NzX3RleHQsIGFueXdpZGdldF9pZCkge1xuXHQvKiogQHR5cGUge0hUTUxTdHlsZUVsZW1lbnQgfCBudWxsfSAqL1xuXHRsZXQgcHJldiA9IGRvY3VtZW50LnF1ZXJ5U2VsZWN0b3IoYHN0eWxlW2lkPScke2FueXdpZGdldF9pZH0nXWApO1xuXHRpZiAocHJldikge1xuXHRcdC8vIHJlcGxhY2UgaW5zdGVhZCBvZiBjcmVhdGluZyBhIG5ldyBET00gbm9kZVxuXHRcdHByZXYudGV4dENvbnRlbnQgPSBjc3NfdGV4dDtcblx0XHRyZXR1cm47XG5cdH1cblx0bGV0IHN0eWxlID0gT2JqZWN0LmFzc2lnbihkb2N1bWVudC5jcmVhdGVFbGVtZW50KFwic3R5bGVcIiksIHtcblx0XHRpZDogYW55d2lkZ2V0X2lkLFxuXHRcdHR5cGU6IFwidGV4dC9jc3NcIixcblx0fSk7XG5cdHN0eWxlLmFwcGVuZENoaWxkKGRvY3VtZW50LmNyZWF0ZVRleHROb2RlKGNzc190ZXh0KSk7XG5cdGRvY3VtZW50LmhlYWQuYXBwZW5kQ2hpbGQoc3R5bGUpO1xufVxuXG4vKipcbiAqIEBwYXJhbSB7c3RyaW5nIHwgdW5kZWZpbmVkfSBjc3NcbiAqIEBwYXJhbSB7c3RyaW5nfSBhbnl3aWRnZXRfaWRcbiAqIEByZXR1cm5zIHtQcm9taXNlPHZvaWQ+fVxuICovXG5hc3luYyBmdW5jdGlvbiBsb2FkX2Nzcyhjc3MsIGFueXdpZGdldF9pZCkge1xuXHRpZiAoIWNzcyB8fCAhYW55d2lkZ2V0X2lkKSByZXR1cm47XG5cdGlmIChpc19ocmVmKGNzcykpIHJldHVybiBsb2FkX2Nzc19ocmVmKGNzcywgYW55d2lkZ2V0X2lkKTtcblx0cmV0dXJuIGxvYWRfY3NzX3RleHQoY3NzLCBhbnl3aWRnZXRfaWQpO1xufVxuXG4vKipcbiAqIEBwYXJhbSB7c3RyaW5nfSBlc21cbiAqIEByZXR1cm5zIHtQcm9taXNlPEFueVdpZGdldE1vZHVsZT59XG4gKi9cbmFzeW5jIGZ1bmN0aW9uIGxvYWRfZXNtKGVzbSkge1xuXHRpZiAoaXNfaHJlZihlc20pKSB7XG5cdFx0cmV0dXJuIGF3YWl0IGltcG9ydCgvKiB3ZWJwYWNrSWdub3JlOiB0cnVlICovIC8qIEB2aXRlLWlnbm9yZSAqLyBlc20pO1xuXHR9XG5cdGxldCB1cmwgPSBVUkwuY3JlYXRlT2JqZWN0VVJMKG5ldyBCbG9iKFtlc21dLCB7IHR5cGU6IFwidGV4dC9qYXZhc2NyaXB0XCIgfSkpO1xuXHRsZXQgbW9kID0gYXdhaXQgaW1wb3J0KC8qIHdlYnBhY2tJZ25vcmU6IHRydWUgKi8gLyogQHZpdGUtaWdub3JlICovIHVybCk7XG5cdFVSTC5yZXZva2VPYmplY3RVUkwodXJsKTtcblx0cmV0dXJuIG1vZDtcbn1cblxuLyoqIEBwYXJhbSB7c3RyaW5nfSBhbnl3aWRnZXRfaWQgKi9cbmZ1bmN0aW9uIHdhcm5fcmVuZGVyX2RlcHJlY2F0aW9uKGFueXdpZGdldF9pZCkge1xuXHRjb25zb2xlLndhcm4oYFxcXG5bYW55d2lkZ2V0XSBEZXByZWNhdGlvbiBXYXJuaW5nIGZvciAke2FueXdpZGdldF9pZH06IERpcmVjdCBleHBvcnQgb2YgYSAncmVuZGVyJyB3aWxsIGxpa2VseSBiZSBkZXByZWNhdGVkIGluIHRoZSBmdXR1cmUuIFRvIG1pZ3JhdGUgLi4uXG5cblJlbW92ZSB0aGUgJ2V4cG9ydCcga2V5d29yZCBmcm9tICdyZW5kZXInXG4tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLVxuXG5leHBvcnQgZnVuY3Rpb24gcmVuZGVyKHsgbW9kZWwsIGVsIH0pIHsgLi4uIH1cbl5eXl5eXlxuXG5DcmVhdGUgYSBkZWZhdWx0IGV4cG9ydCB0aGF0IHJldHVybnMgYW4gb2JqZWN0IHdpdGggJ3JlbmRlcidcbi0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLVxuXG5mdW5jdGlvbiByZW5kZXIoeyBtb2RlbCwgZWwgfSkgeyAuLi4gfVxuICAgICAgICAgXl5eXl5eXG5leHBvcnQgZGVmYXVsdCB7IHJlbmRlciB9XG4gICAgICAgICAgICAgICAgIF5eXl5eXlxuXG5QaW4gdG8gYW55d2lkZ2V0Pj0wLjkuMCBpbiB5b3VyIHB5cHJvamVjdC50b21sXG4tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tXG5cbmRlcGVuZGVuY2llcyA9IFtcImFueXdpZGdldD49MC45LjBcIl1cblxuVG8gbGVhcm4gbW9yZSwgcGxlYXNlIHNlZTogaHR0cHM6Ly9naXRodWIuY29tL21hbnp0L2FueXdpZGdldC9wdWxsLzM5NS5cbmApO1xufVxuXG4vKipcbiAqIEBwYXJhbSB7c3RyaW5nfSBlc21cbiAqIEBwYXJhbSB7c3RyaW5nfSBhbnl3aWRnZXRfaWRcbiAqIEByZXR1cm5zIHtQcm9taXNlPEFueVdpZGdldD59XG4gKi9cbmFzeW5jIGZ1bmN0aW9uIGxvYWRfd2lkZ2V0KGVzbSwgYW55d2lkZ2V0X2lkKSB7XG5cdGxldCBtb2QgPSBhd2FpdCBsb2FkX2VzbShlc20pO1xuXHRpZiAobW9kLnJlbmRlcikge1xuXHRcdHdhcm5fcmVuZGVyX2RlcHJlY2F0aW9uKGFueXdpZGdldF9pZCk7XG5cdFx0cmV0dXJuIHtcblx0XHRcdGFzeW5jIGluaXRpYWxpemUoKSB7fSxcblx0XHRcdHJlbmRlcjogbW9kLnJlbmRlcixcblx0XHR9O1xuXHR9XG5cdGFzc2VydChcblx0XHRtb2QuZGVmYXVsdCxcblx0XHRgW2FueXdpZGdldF0gbW9kdWxlIG11c3QgZXhwb3J0IGEgZGVmYXVsdCBmdW5jdGlvbiBvciBvYmplY3QuYCxcblx0KTtcblx0bGV0IHdpZGdldCA9XG5cdFx0dHlwZW9mIG1vZC5kZWZhdWx0ID09PSBcImZ1bmN0aW9uXCIgPyBhd2FpdCBtb2QuZGVmYXVsdCgpIDogbW9kLmRlZmF1bHQ7XG5cdHJldHVybiB3aWRnZXQ7XG59XG5cbi8qKlxuICogVGhpcyBpcyBhIHRyaWNrIHNvIHRoYXQgd2UgY2FuIGNsZWFudXAgZXZlbnQgbGlzdGVuZXJzIGFkZGVkXG4gKiBieSB0aGUgdXNlci1kZWZpbmVkIGZ1bmN0aW9uLlxuICovXG5sZXQgSU5JVElBTElaRV9NQVJLRVIgPSBTeW1ib2woXCJhbnl3aWRnZXQuaW5pdGlhbGl6ZVwiKTtcblxuLyoqXG4gKiBAcGFyYW0ge2Jhc2UuRE9NV2lkZ2V0TW9kZWx9IG1vZGVsXG4gKiBAcGFyYW0ge3Vua25vd259IGNvbnRleHRcbiAqIEByZXR1cm4ge2ltcG9ydChcIkBhbnl3aWRnZXQvdHlwZXNcIikuQW55TW9kZWx9XG4gKlxuICogUHJ1bmVzIHRoZSB2aWV3IGRvd24gdG8gdGhlIG1pbmltdW0gY29udGV4dCBuZWNlc3NhcnkuXG4gKlxuICogQ2FsbHMgdG8gYG1vZGVsLmdldGAgYW5kIGBtb2RlbC5zZXRgIGF1dG9tYXRpY2FsbHkgYWRkIHRoZVxuICogYGNvbnRleHRgLCBzbyB3ZSBjYW4gZ3JhY2VmdWxseSB1bnN1YnNjcmliZSBmcm9tIGV2ZW50c1xuICogYWRkZWQgYnkgdXNlci1kZWZpbmVkIGhvb2tzLlxuICovXG5mdW5jdGlvbiBtb2RlbF9wcm94eShtb2RlbCwgY29udGV4dCkge1xuXHRyZXR1cm4ge1xuXHRcdGdldDogbW9kZWwuZ2V0LmJpbmQobW9kZWwpLFxuXHRcdHNldDogbW9kZWwuc2V0LmJpbmQobW9kZWwpLFxuXHRcdHNhdmVfY2hhbmdlczogbW9kZWwuc2F2ZV9jaGFuZ2VzLmJpbmQobW9kZWwpLFxuXHRcdHNlbmQ6IG1vZGVsLnNlbmQuYmluZChtb2RlbCksXG5cdFx0Ly8gQHRzLWV4cGVjdC1lcnJvclxuXHRcdG9uKG5hbWUsIGNhbGxiYWNrKSB7XG5cdFx0XHRtb2RlbC5vbihuYW1lLCBjYWxsYmFjaywgY29udGV4dCk7XG5cdFx0fSxcblx0XHRvZmYobmFtZSwgY2FsbGJhY2spIHtcblx0XHRcdG1vZGVsLm9mZihuYW1lLCBjYWxsYmFjaywgY29udGV4dCk7XG5cdFx0fSxcblx0XHQvLyBAdHMtZXhwZWN0LWVycm9yIC0gdGhlIHdpZGdldF9tYW5hZ2VyIHR5cGUgaXMgd2lkZXIgdGhhbiB3aGF0XG5cdFx0Ly8gd2Ugd2FudCB0byBleHBvc2UgdG8gZGV2ZWxvcGVycy5cblx0XHQvLyBJbiBhIGZ1dHVyZSB2ZXJzaW9uLCB3ZSB3aWxsIGV4cG9zZSBhIG1vcmUgbGltaXRlZCBBUEkgYnV0XG5cdFx0Ly8gdGhhdCBjYW4gd2FpdCBmb3IgYSBtaW5vciB2ZXJzaW9uIGJ1bXAuXG5cdFx0d2lkZ2V0X21hbmFnZXI6IG1vZGVsLndpZGdldF9tYW5hZ2VyLFxuXHR9O1xufVxuXG4vKipcbiAqIEBwYXJhbSB7dm9pZCB8ICgoKSA9PiBBd2FpdGFibGU8dm9pZD4pfSBmblxuICogQHBhcmFtIHtzdHJpbmd9IGtpbmRcbiAqL1xuYXN5bmMgZnVuY3Rpb24gc2FmZV9jbGVhbnVwKGZuLCBraW5kKSB7XG5cdHJldHVybiBQcm9taXNlLnJlc29sdmUoKVxuXHRcdC50aGVuKCgpID0+IGZuPy4oKSlcblx0XHQuY2F0Y2goKGUpID0+IGNvbnNvbGUud2FybihgW2FueXdpZGdldF0gZXJyb3IgY2xlYW5pbmcgdXAgJHtraW5kfS5gLCBlKSk7XG59XG5cbi8qKlxuICogQHRlbXBsYXRlIFRcbiAqIEB0eXBlZGVmIFJlYWR5XG4gKiBAcHJvcGVydHkge1wicmVhZHlcIn0gc3RhdHVzXG4gKiBAcHJvcGVydHkge1R9IGRhdGFcbiAqL1xuXG4vKipcbiAqIEB0eXBlZGVmIFBlbmRpbmdcbiAqIEBwcm9wZXJ0eSB7XCJwZW5kaW5nXCJ9IHN0YXR1c1xuICovXG5cbi8qKlxuICogQHR5cGVkZWYgRXJyb3JlZFxuICogQHByb3BlcnR5IHtcImVycm9yXCJ9IHN0YXR1c1xuICogQHByb3BlcnR5IHt1bmtub3dufSBlcnJvclxuICovXG5cbi8qKlxuICogQHRlbXBsYXRlIFRcbiAqIEB0eXBlZGVmIHtQZW5kaW5nIHwgUmVhZHk8VD4gfCBFcnJvcmVkfSBSZXN1bHRcbiAqL1xuXG4vKipcbiAqIENsZWFucyB1cCB0aGUgc3RhY2sgdHJhY2UgYXQgYW55d2lkZ2V0IGJvdW5kYXJ5LlxuICogWW91IGNhbiBmdWxseSBpbnNwZWN0IHRoZSBlbnRpcmUgc3RhY2sgdHJhY2UgaW4gdGhlIGNvbnNvbGUgaW50ZXJhY3RpdmVseSxcbiAqIGJ1dCB0aGUgaW5pdGlhbCBlcnJvciBtZXNzYWdlIGlzIGNsZWFuZWQgdXAgdG8gYmUgbW9yZSB1c2VyLWZyaWVuZGx5LlxuICpcbiAqIEBwYXJhbSB7dW5rbm93bn0gc291cmNlXG4gKi9cbmZ1bmN0aW9uIHRocm93X2FueXdpZGdldF9lcnJvcihzb3VyY2UpIHtcblx0aWYgKCEoc291cmNlIGluc3RhbmNlb2YgRXJyb3IpKSB7XG5cdFx0Ly8gRG9uJ3Qga25vdyB3aGF0IHRvIGRvIHdpdGggdGhpcy5cblx0XHR0aHJvdyBzb3VyY2U7XG5cdH1cblx0bGV0IGxpbmVzID0gc291cmNlLnN0YWNrPy5zcGxpdChcIlxcblwiKSA/PyBbXTtcblx0bGV0IGFueXdpZGdldF9pbmRleCA9IGxpbmVzLmZpbmRJbmRleCgobGluZSkgPT4gbGluZS5pbmNsdWRlcyhcImFueXdpZGdldFwiKSk7XG5cdGxldCBjbGVhbl9zdGFjayA9XG5cdFx0YW55d2lkZ2V0X2luZGV4ID09PSAtMSA/IGxpbmVzIDogbGluZXMuc2xpY2UoMCwgYW55d2lkZ2V0X2luZGV4ICsgMSk7XG5cdHNvdXJjZS5zdGFjayA9IGNsZWFuX3N0YWNrLmpvaW4oXCJcXG5cIik7XG5cdGNvbnNvbGUuZXJyb3Ioc291cmNlKTtcblx0dGhyb3cgc291cmNlO1xufVxuXG4vKipcbiAqIEB0eXBlZGVmIEludm9rZU9wdGlvbnNcbiAqIEBwcm9wIHtEYXRhVmlld1tdfSBbYnVmZmVyc11cbiAqIEBwcm9wIHtBYm9ydFNpZ25hbH0gW3NpZ25hbF1cbiAqL1xuXG4vKipcbiAqIEB0ZW1wbGF0ZSBUXG4gKiBAcGFyYW0ge2ltcG9ydChcIkBhbnl3aWRnZXQvdHlwZXNcIikuQW55TW9kZWx9IG1vZGVsXG4gKiBAcGFyYW0ge3N0cmluZ30gbmFtZVxuICogQHBhcmFtIHthbnl9IFttc2ddXG4gKiBAcGFyYW0ge0ludm9rZU9wdGlvbnN9IFtvcHRpb25zXVxuICogQHJldHVybiB7UHJvbWlzZTxbVCwgRGF0YVZpZXdbXV0+fVxuICovXG5leHBvcnQgZnVuY3Rpb24gaW52b2tlKG1vZGVsLCBuYW1lLCBtc2csIG9wdGlvbnMgPSB7fSkge1xuXHQvLyBjcnlwdG8ucmFuZG9tVVVJRCgpIGlzIG5vdCBhdmFpbGFibGUgaW4gbm9uLXNlY3VyZSBjb250ZXh0cyAoaS5lLiwgaHR0cDovLylcblx0Ly8gc28gd2UgdXNlIHNpbXBsZSAobm9uLXNlY3VyZSkgcG9seWZpbGwuXG5cdGxldCBpZCA9IHV1aWQudjQoKTtcblx0bGV0IHNpZ25hbCA9IG9wdGlvbnMuc2lnbmFsID8/IEFib3J0U2lnbmFsLnRpbWVvdXQoMzAwMCk7XG5cblx0cmV0dXJuIG5ldyBQcm9taXNlKChyZXNvbHZlLCByZWplY3QpID0+IHtcblx0XHRpZiAoc2lnbmFsLmFib3J0ZWQpIHtcblx0XHRcdHJlamVjdChzaWduYWwucmVhc29uKTtcblx0XHR9XG5cdFx0c2lnbmFsLmFkZEV2ZW50TGlzdGVuZXIoXCJhYm9ydFwiLCAoKSA9PiB7XG5cdFx0XHRtb2RlbC5vZmYoXCJtc2c6Y3VzdG9tXCIsIGhhbmRsZXIpO1xuXHRcdFx0cmVqZWN0KHNpZ25hbC5yZWFzb24pO1xuXHRcdH0pO1xuXG5cdFx0LyoqXG5cdFx0ICogQHBhcmFtIHt7IGlkOiBzdHJpbmcsIGtpbmQ6IFwiYW55d2lkZ2V0LWNvbW1hbmQtcmVzcG9uc2VcIiwgcmVzcG9uc2U6IFQgfX0gbXNnXG5cdFx0ICogQHBhcmFtIHtEYXRhVmlld1tdfSBidWZmZXJzXG5cdFx0ICovXG5cdFx0ZnVuY3Rpb24gaGFuZGxlcihtc2csIGJ1ZmZlcnMpIHtcblx0XHRcdGlmICghKG1zZy5pZCA9PT0gaWQpKSByZXR1cm47XG5cdFx0XHRyZXNvbHZlKFttc2cucmVzcG9uc2UsIGJ1ZmZlcnNdKTtcblx0XHRcdG1vZGVsLm9mZihcIm1zZzpjdXN0b21cIiwgaGFuZGxlcik7XG5cdFx0fVxuXHRcdG1vZGVsLm9uKFwibXNnOmN1c3RvbVwiLCBoYW5kbGVyKTtcblx0XHRtb2RlbC5zZW5kKFxuXHRcdFx0eyBpZCwga2luZDogXCJhbnl3aWRnZXQtY29tbWFuZFwiLCBuYW1lLCBtc2cgfSxcblx0XHRcdHVuZGVmaW5lZCxcblx0XHRcdG9wdGlvbnMuYnVmZmVycyA/PyBbXSxcblx0XHQpO1xuXHR9KTtcbn1cblxuLyoqXG4gKiBQb2x5ZmlsbCBmb3Ige0BsaW5rIGh0dHBzOi8vZGV2ZWxvcGVyLm1vemlsbGEub3JnL2VuLVVTL2RvY3MvV2ViL0phdmFTY3JpcHQvUmVmZXJlbmNlL0dsb2JhbF9PYmplY3RzL1Byb21pc2Uvd2l0aFJlc29sdmVycyBQcm9taXNlLndpdGhSZXNvbHZlcnN9XG4gKlxuICogVHJldm9yKDIwMjUtMDMtMTQpOiBTaG91bGQgYmUgYWJsZSB0byByZW1vdmUgb25jZSBtb3JlIHN0YWJsZSBhY3Jvc3MgYnJvd3NlcnMuXG4gKlxuICogQHRlbXBsYXRlIFRcbiAqIEByZXR1cm5zIHtQcm9taXNlV2l0aFJlc29sdmVyczxUPn1cbiAqL1xuZnVuY3Rpb24gcHJvbWlzZV93aXRoX3Jlc29sdmVycygpIHtcblx0bGV0IHJlc29sdmU7XG5cdGxldCByZWplY3Q7XG5cdGxldCBwcm9taXNlID0gbmV3IFByb21pc2UoKHJlcywgcmVqKSA9PiB7XG5cdFx0cmVzb2x2ZSA9IHJlcztcblx0XHRyZWplY3QgPSByZWo7XG5cdH0pO1xuXHQvLyBAdHMtZXhwZWN0LWVycm9yIC0gV2Uga25vdyB0aGVzZSB0eXBlcyBhcmUgb2tcblx0cmV0dXJuIHsgcHJvbWlzZSwgcmVzb2x2ZSwgcmVqZWN0IH07XG59XG5cbi8qKlxuICogQHRlbXBsYXRlIHtSZWNvcmQ8c3RyaW5nLCB1bmtub3duPn0gVFxuICogQHRlbXBsYXRlIHtrZXlvZiBUICYgc3RyaW5nfSBLXG4gKiBAcGFyYW0ge0FueU1vZGVsPFQ+fSBtb2RlbFxuICogQHBhcmFtIHtLfSBuYW1lXG4gKiBAcGFyYW0ge3sgc2lnbmFsPzogQWJvcnRTaWduYWx9fSBvcHRpb25zXG4gKiBAcmV0dXJucyB7c29saWQuQWNjZXNzb3I8VFtLXT59XG4gKi9cbmZ1bmN0aW9uIG9ic2VydmUobW9kZWwsIG5hbWUsIHsgc2lnbmFsIH0pIHtcblx0bGV0IFtnZXQsIHNldF0gPSBzb2xpZC5jcmVhdGVTaWduYWwobW9kZWwuZ2V0KG5hbWUpKTtcblx0bGV0IHVwZGF0ZSA9ICgpID0+IHNldCgoKSA9PiBtb2RlbC5nZXQobmFtZSkpO1xuXHRtb2RlbC5vbihgY2hhbmdlOiR7bmFtZX1gLCB1cGRhdGUpO1xuXHRzaWduYWw/LmFkZEV2ZW50TGlzdGVuZXIoXCJhYm9ydFwiLCAoKSA9PiB7XG5cdFx0bW9kZWwub2ZmKGBjaGFuZ2U6JHtuYW1lfWAsIHVwZGF0ZSk7XG5cdH0pO1xuXHRyZXR1cm4gZ2V0O1xufVxuXG4vKipcbiAqIEB0eXBlZGVmIFN0YXRlXG4gKiBAcHJvcGVydHkge3N0cmluZ30gX2VzbVxuICogQHByb3BlcnR5IHtzdHJpbmd9IF9hbnl3aWRnZXRfaWRcbiAqIEBwcm9wZXJ0eSB7c3RyaW5nIHwgdW5kZWZpbmVkfSBfY3NzXG4gKi9cblxuY2xhc3MgUnVudGltZSB7XG5cdC8qKiBAdHlwZSB7c29saWQuQWNjZXNzb3I8UmVzdWx0PEFueVdpZGdldD4+fSAqL1xuXHQvLyBAdHMtZXhwZWN0LWVycm9yIC0gU2V0IHN5bmNocm9ub3VzbHkgaW4gY29uc3RydWN0b3IuXG5cdCN3aWRnZXRfcmVzdWx0O1xuXHQvKiogQHR5cGUge0Fib3J0U2lnbmFsfSAqL1xuXHQjc2lnbmFsO1xuXHQvKiogQHR5cGUge1Byb21pc2U8dm9pZD59ICovXG5cdHJlYWR5O1xuXG5cdC8qKlxuXHQgKiBAcGFyYW0ge2Jhc2UuRE9NV2lkZ2V0TW9kZWx9IG1vZGVsXG5cdCAqIEBwYXJhbSB7eyBzaWduYWw6IEFib3J0U2lnbmFsIH19IG9wdGlvbnNcblx0ICovXG5cdGNvbnN0cnVjdG9yKG1vZGVsLCBvcHRpb25zKSB7XG5cdFx0LyoqIEB0eXBlIHtQcm9taXNlV2l0aFJlc29sdmVyczx2b2lkPn0gKi9cblx0XHRsZXQgcmVzb2x2ZXJzID0gcHJvbWlzZV93aXRoX3Jlc29sdmVycygpO1xuXHRcdHRoaXMucmVhZHkgPSByZXNvbHZlcnMucHJvbWlzZTtcblx0XHR0aGlzLiNzaWduYWwgPSBvcHRpb25zLnNpZ25hbDtcblx0XHR0aGlzLiNzaWduYWwudGhyb3dJZkFib3J0ZWQoKTtcblx0XHR0aGlzLiNzaWduYWwuYWRkRXZlbnRMaXN0ZW5lcihcImFib3J0XCIsICgpID0+IGRpc3Bvc2UoKSk7XG5cdFx0QWJvcnRTaWduYWwudGltZW91dCgyMDAwKS5hZGRFdmVudExpc3RlbmVyKFwiYWJvcnRcIiwgKCkgPT4ge1xuXHRcdFx0cmVzb2x2ZXJzLnJlamVjdChuZXcgRXJyb3IoXCJbYW55d2lkZ2V0XSBGYWlsZWQgdG8gaW5pdGlhbGl6ZSBtb2RlbC5cIikpO1xuXHRcdH0pO1xuXHRcdGxldCBkaXNwb3NlID0gc29saWQuY3JlYXRlUm9vdCgoZGlzcG9zZSkgPT4ge1xuXHRcdFx0LyoqIEB0eXBlIHtBbnlNb2RlbDxTdGF0ZT59ICovXG5cdFx0XHQvLyBAdHMtZXhwZWN0LWVycm9yIC0gVHlwZXMgZG9uJ3Qgc3VmZmljaWVudGx5IG92ZXJsYXAsIHNvIHdlIGNhc3QgaGVyZSBmb3IgdHlwZS1zYWZlIGFjY2Vzc1xuXHRcdFx0bGV0IHR5cGVkX21vZGVsID0gbW9kZWw7XG5cdFx0XHRsZXQgaWQgPSB0eXBlZF9tb2RlbC5nZXQoXCJfYW55d2lkZ2V0X2lkXCIpO1xuXHRcdFx0bGV0IGNzcyA9IG9ic2VydmUodHlwZWRfbW9kZWwsIFwiX2Nzc1wiLCB7IHNpZ25hbDogdGhpcy4jc2lnbmFsIH0pO1xuXHRcdFx0bGV0IGVzbSA9IG9ic2VydmUodHlwZWRfbW9kZWwsIFwiX2VzbVwiLCB7IHNpZ25hbDogdGhpcy4jc2lnbmFsIH0pO1xuXHRcdFx0bGV0IFt3aWRnZXRfcmVzdWx0LCBzZXRfd2lkZ2V0X3Jlc3VsdF0gPSBzb2xpZC5jcmVhdGVTaWduYWwoXG5cdFx0XHRcdC8qKiBAdHlwZSB7UmVzdWx0PEFueVdpZGdldD59ICovICh7IHN0YXR1czogXCJwZW5kaW5nXCIgfSksXG5cdFx0XHQpO1xuXHRcdFx0dGhpcy4jd2lkZ2V0X3Jlc3VsdCA9IHdpZGdldF9yZXN1bHQ7XG5cblx0XHRcdHNvbGlkLmNyZWF0ZUVmZmVjdChcblx0XHRcdFx0c29saWQub24oXG5cdFx0XHRcdFx0Y3NzLFxuXHRcdFx0XHRcdCgpID0+IGNvbnNvbGUuZGVidWcoYFthbnl3aWRnZXRdIGNzcyBob3QgdXBkYXRlZDogJHtpZH1gKSxcblx0XHRcdFx0XHR7IGRlZmVyOiB0cnVlIH0sXG5cdFx0XHRcdCksXG5cdFx0XHQpO1xuXHRcdFx0c29saWQuY3JlYXRlRWZmZWN0KFxuXHRcdFx0XHRzb2xpZC5vbihcblx0XHRcdFx0XHRlc20sXG5cdFx0XHRcdFx0KCkgPT4gY29uc29sZS5kZWJ1ZyhgW2FueXdpZGdldF0gZXNtIGhvdCB1cGRhdGVkOiAke2lkfWApLFxuXHRcdFx0XHRcdHsgZGVmZXI6IHRydWUgfSxcblx0XHRcdFx0KSxcblx0XHRcdCk7XG5cdFx0XHRzb2xpZC5jcmVhdGVFZmZlY3QoKCkgPT4ge1xuXHRcdFx0XHRsb2FkX2Nzcyhjc3MoKSwgaWQpO1xuXHRcdFx0fSk7XG5cdFx0XHRzb2xpZC5jcmVhdGVFZmZlY3QoKCkgPT4ge1xuXHRcdFx0XHRsZXQgY29udHJvbGxlciA9IG5ldyBBYm9ydENvbnRyb2xsZXIoKTtcblx0XHRcdFx0c29saWQub25DbGVhbnVwKCgpID0+IGNvbnRyb2xsZXIuYWJvcnQoKSk7XG5cdFx0XHRcdG1vZGVsLm9mZihudWxsLCBudWxsLCBJTklUSUFMSVpFX01BUktFUik7XG5cdFx0XHRcdGxvYWRfd2lkZ2V0KGVzbSgpLCBpZClcblx0XHRcdFx0XHQudGhlbihhc3luYyAod2lkZ2V0KSA9PiB7XG5cdFx0XHRcdFx0XHRpZiAoY29udHJvbGxlci5zaWduYWwuYWJvcnRlZCkge1xuXHRcdFx0XHRcdFx0XHRyZXR1cm47XG5cdFx0XHRcdFx0XHR9XG5cdFx0XHRcdFx0XHRsZXQgY2xlYW51cCA9IGF3YWl0IHdpZGdldC5pbml0aWFsaXplPy4oe1xuXHRcdFx0XHRcdFx0XHRtb2RlbDogbW9kZWxfcHJveHkobW9kZWwsIElOSVRJQUxJWkVfTUFSS0VSKSxcblx0XHRcdFx0XHRcdFx0ZXhwZXJpbWVudGFsOiB7XG5cdFx0XHRcdFx0XHRcdFx0Ly8gQHRzLWV4cGVjdC1lcnJvciAtIGJpbmQgaXNuJ3Qgd29ya2luZ1xuXHRcdFx0XHRcdFx0XHRcdGludm9rZTogaW52b2tlLmJpbmQobnVsbCwgbW9kZWwpLFxuXHRcdFx0XHRcdFx0XHR9LFxuXHRcdFx0XHRcdFx0fSk7XG5cdFx0XHRcdFx0XHRpZiAoY29udHJvbGxlci5zaWduYWwuYWJvcnRlZCkge1xuXHRcdFx0XHRcdFx0XHRzYWZlX2NsZWFudXAoY2xlYW51cCwgXCJlc20gdXBkYXRlXCIpO1xuXHRcdFx0XHRcdFx0XHRyZXR1cm47XG5cdFx0XHRcdFx0XHR9XG5cdFx0XHRcdFx0XHRjb250cm9sbGVyLnNpZ25hbC5hZGRFdmVudExpc3RlbmVyKFwiYWJvcnRcIiwgKCkgPT5cblx0XHRcdFx0XHRcdFx0c2FmZV9jbGVhbnVwKGNsZWFudXAsIFwiZXNtIHVwZGF0ZVwiKSxcblx0XHRcdFx0XHRcdCk7XG5cdFx0XHRcdFx0XHRzZXRfd2lkZ2V0X3Jlc3VsdCh7IHN0YXR1czogXCJyZWFkeVwiLCBkYXRhOiB3aWRnZXQgfSk7XG5cdFx0XHRcdFx0XHRyZXNvbHZlcnMucmVzb2x2ZSgpO1xuXHRcdFx0XHRcdH0pXG5cdFx0XHRcdFx0LmNhdGNoKChlcnJvcikgPT4gc2V0X3dpZGdldF9yZXN1bHQoeyBzdGF0dXM6IFwiZXJyb3JcIiwgZXJyb3IgfSkpO1xuXHRcdFx0fSk7XG5cblx0XHRcdHJldHVybiBkaXNwb3NlO1xuXHRcdH0pO1xuXHR9XG5cblx0LyoqXG5cdCAqIEBwYXJhbSB7YmFzZS5ET01XaWRnZXRWaWV3fSB2aWV3XG5cdCAqIEBwYXJhbSB7eyBzaWduYWw6IEFib3J0U2lnbmFsIH19IG9wdGlvbnNcblx0ICogQHJldHVybnMge1Byb21pc2U8dm9pZD59XG5cdCAqL1xuXHRhc3luYyBjcmVhdGVfdmlldyh2aWV3LCBvcHRpb25zKSB7XG5cdFx0bGV0IG1vZGVsID0gdmlldy5tb2RlbDtcblx0XHRsZXQgc2lnbmFsID0gQWJvcnRTaWduYWwuYW55KFt0aGlzLiNzaWduYWwsIG9wdGlvbnMuc2lnbmFsXSk7IC8vIGVpdGhlciBtb2RlbCBvciB2aWV3IGRlc3Ryb3llZFxuXHRcdHNpZ25hbC50aHJvd0lmQWJvcnRlZCgpO1xuXHRcdHNpZ25hbC5hZGRFdmVudExpc3RlbmVyKFwiYWJvcnRcIiwgKCkgPT4gZGlzcG9zZSgpKTtcblx0XHRsZXQgZGlzcG9zZSA9IHNvbGlkLmNyZWF0ZVJvb3QoKGRpc3Bvc2UpID0+IHtcblx0XHRcdHNvbGlkLmNyZWF0ZUVmZmVjdCgoKSA9PiB7XG5cdFx0XHRcdC8vIENsZWFyIGFsbCBwcmV2aW91cyBldmVudCBsaXN0ZW5lcnMgZnJvbSB0aGlzIGhvb2suXG5cdFx0XHRcdG1vZGVsLm9mZihudWxsLCBudWxsLCB2aWV3KTtcblx0XHRcdFx0dmlldy4kZWwuZW1wdHkoKTtcblx0XHRcdFx0bGV0IHJlc3VsdCA9IHRoaXMuI3dpZGdldF9yZXN1bHQoKTtcblx0XHRcdFx0aWYgKHJlc3VsdC5zdGF0dXMgPT09IFwicGVuZGluZ1wiKSB7XG5cdFx0XHRcdFx0cmV0dXJuO1xuXHRcdFx0XHR9XG5cdFx0XHRcdGlmIChyZXN1bHQuc3RhdHVzID09PSBcImVycm9yXCIpIHtcblx0XHRcdFx0XHR0aHJvd19hbnl3aWRnZXRfZXJyb3IocmVzdWx0LmVycm9yKTtcblx0XHRcdFx0XHRyZXR1cm47XG5cdFx0XHRcdH1cblx0XHRcdFx0bGV0IGNvbnRyb2xsZXIgPSBuZXcgQWJvcnRDb250cm9sbGVyKCk7XG5cdFx0XHRcdHNvbGlkLm9uQ2xlYW51cCgoKSA9PiBjb250cm9sbGVyLmFib3J0KCkpO1xuXHRcdFx0XHRQcm9taXNlLnJlc29sdmUoKVxuXHRcdFx0XHRcdC50aGVuKGFzeW5jICgpID0+IHtcblx0XHRcdFx0XHRcdGxldCBjbGVhbnVwID0gYXdhaXQgcmVzdWx0LmRhdGEucmVuZGVyPy4oe1xuXHRcdFx0XHRcdFx0XHRtb2RlbDogbW9kZWxfcHJveHkobW9kZWwsIHZpZXcpLFxuXHRcdFx0XHRcdFx0XHRlbDogdmlldy5lbCxcblx0XHRcdFx0XHRcdFx0ZXhwZXJpbWVudGFsOiB7XG5cdFx0XHRcdFx0XHRcdFx0Ly8gQHRzLWV4cGVjdC1lcnJvciAtIGJpbmQgaXNuJ3Qgd29ya2luZ1xuXHRcdFx0XHRcdFx0XHRcdGludm9rZTogaW52b2tlLmJpbmQobnVsbCwgbW9kZWwpLFxuXHRcdFx0XHRcdFx0XHR9LFxuXHRcdFx0XHRcdFx0fSk7XG5cdFx0XHRcdFx0XHRpZiAoY29udHJvbGxlci5zaWduYWwuYWJvcnRlZCkge1xuXHRcdFx0XHRcdFx0XHRzYWZlX2NsZWFudXAoY2xlYW51cCwgXCJkaXNwb3NlIHZpZXcgLSBhbHJlYWR5IGFib3J0ZWRcIik7XG5cdFx0XHRcdFx0XHRcdHJldHVybjtcblx0XHRcdFx0XHRcdH1cblx0XHRcdFx0XHRcdGNvbnRyb2xsZXIuc2lnbmFsLmFkZEV2ZW50TGlzdGVuZXIoXCJhYm9ydFwiLCAoKSA9PlxuXHRcdFx0XHRcdFx0XHRzYWZlX2NsZWFudXAoY2xlYW51cCwgXCJkaXNwb3NlIHZpZXcgLSBhYm9ydGVkXCIpLFxuXHRcdFx0XHRcdFx0KTtcblx0XHRcdFx0XHR9KVxuXHRcdFx0XHRcdC5jYXRjaCgoZXJyb3IpID0+IHRocm93X2FueXdpZGdldF9lcnJvcihlcnJvcikpO1xuXHRcdFx0fSk7XG5cdFx0XHRyZXR1cm4gKCkgPT4gZGlzcG9zZSgpO1xuXHRcdH0pO1xuXHR9XG59XG5cbi8vIEB0cy1leHBlY3QtZXJyb3IgLSBpbmplY3RlZCBieSBidW5kbGVyXG5sZXQgdmVyc2lvbiA9IGdsb2JhbFRoaXMuVkVSU0lPTjtcblxuLyoqXG4gKiBAcGFyYW0ge2Jhc2V9IG9wdGlvbnNcbiAqIEByZXR1cm5zIHt7IEFueU1vZGVsOiB0eXBlb2YgYmFzZS5ET01XaWRnZXRNb2RlbCwgQW55VmlldzogdHlwZW9mIGJhc2UuRE9NV2lkZ2V0VmlldyB9fVxuICovXG5leHBvcnQgZGVmYXVsdCBmdW5jdGlvbiAoeyBET01XaWRnZXRNb2RlbCwgRE9NV2lkZ2V0VmlldyB9KSB7XG5cdC8qKiBAdHlwZSB7V2Vha01hcDxBbnlNb2RlbCwgUnVudGltZT59ICovXG5cdGxldCBSVU5USU1FUyA9IG5ldyBXZWFrTWFwKCk7XG5cblx0Y2xhc3MgQW55TW9kZWwgZXh0ZW5kcyBET01XaWRnZXRNb2RlbCB7XG5cdFx0c3RhdGljIG1vZGVsX25hbWUgPSBcIkFueU1vZGVsXCI7XG5cdFx0c3RhdGljIG1vZGVsX21vZHVsZSA9IFwiYW55d2lkZ2V0XCI7XG5cdFx0c3RhdGljIG1vZGVsX21vZHVsZV92ZXJzaW9uID0gdmVyc2lvbjtcblxuXHRcdHN0YXRpYyB2aWV3X25hbWUgPSBcIkFueVZpZXdcIjtcblx0XHRzdGF0aWMgdmlld19tb2R1bGUgPSBcImFueXdpZGdldFwiO1xuXHRcdHN0YXRpYyB2aWV3X21vZHVsZV92ZXJzaW9uID0gdmVyc2lvbjtcblxuXHRcdC8qKiBAcGFyYW0ge1BhcmFtZXRlcnM8SW5zdGFuY2VUeXBlPERPTVdpZGdldE1vZGVsPltcImluaXRpYWxpemVcIl0+fSBhcmdzICovXG5cdFx0aW5pdGlhbGl6ZSguLi5hcmdzKSB7XG5cdFx0XHRzdXBlci5pbml0aWFsaXplKC4uLmFyZ3MpO1xuXHRcdFx0bGV0IGNvbnRyb2xsZXIgPSBuZXcgQWJvcnRDb250cm9sbGVyKCk7XG5cdFx0XHR0aGlzLm9uY2UoXCJkZXN0cm95XCIsICgpID0+IHtcblx0XHRcdFx0Y29udHJvbGxlci5hYm9ydChcIlthbnl3aWRnZXRdIFJ1bnRpbWUgZGVzdHJveWVkLlwiKTtcblx0XHRcdFx0UlVOVElNRVMuZGVsZXRlKHRoaXMpO1xuXHRcdFx0fSk7XG5cdFx0XHRSVU5USU1FUy5zZXQodGhpcywgbmV3IFJ1bnRpbWUodGhpcywgeyBzaWduYWw6IGNvbnRyb2xsZXIuc2lnbmFsIH0pKTtcblx0XHR9XG5cblx0XHQvKiogQHBhcmFtIHtQYXJhbWV0ZXJzPEluc3RhbmNlVHlwZTxET01XaWRnZXRNb2RlbD5bXCJfaGFuZGxlX2NvbW1fbXNnXCJdPn0gbXNnICovXG5cdFx0YXN5bmMgX2hhbmRsZV9jb21tX21zZyguLi5tc2cpIHtcblx0XHRcdGxldCBydW50aW1lID0gUlVOVElNRVMuZ2V0KHRoaXMpO1xuXHRcdFx0YXdhaXQgcnVudGltZT8ucmVhZHk7XG5cdFx0XHRyZXR1cm4gc3VwZXIuX2hhbmRsZV9jb21tX21zZyguLi5tc2cpO1xuXHRcdH1cblxuXHRcdC8qKlxuXHRcdCAqIEBwYXJhbSB7UmVjb3JkPHN0cmluZywgYW55Pn0gc3RhdGVcblx0XHQgKlxuXHRcdCAqIFdlIG92ZXJyaWRlIHRvIHN1cHBvcnQgYmluYXJ5IHRyYWlsZXRzIGJlY2F1c2UgSlNPTi5wYXJzZShKU09OLnN0cmluZ2lmeSgpKVxuXHRcdCAqIGRvZXMgbm90IHByb3Blcmx5IGNsb25lIGJpbmFyeSBkYXRhIChpdCBqdXN0IHJldHVybnMgYW4gZW1wdHkgb2JqZWN0KS5cblx0XHQgKlxuXHRcdCAqIGh0dHBzOi8vZ2l0aHViLmNvbS9qdXB5dGVyLXdpZGdldHMvaXB5d2lkZ2V0cy9ibG9iLzQ3MDU4YTM3M2QyYzJiM2FjZjEwMTY3N2IyNzQ1ZTE0Yjc2ZGQ3NGIvcGFja2FnZXMvYmFzZS9zcmMvd2lkZ2V0LnRzI0w1NjItTDU4M1xuXHRcdCAqL1xuXHRcdHNlcmlhbGl6ZShzdGF0ZSkge1xuXHRcdFx0bGV0IHNlcmlhbGl6ZXJzID1cblx0XHRcdFx0LyoqIEB0eXBlIHtET01XaWRnZXRNb2RlbH0gKi8gKHRoaXMuY29uc3RydWN0b3IpLnNlcmlhbGl6ZXJzIHx8IHt9O1xuXHRcdFx0Zm9yIChsZXQgayBvZiBPYmplY3Qua2V5cyhzdGF0ZSkpIHtcblx0XHRcdFx0dHJ5IHtcblx0XHRcdFx0XHRsZXQgc2VyaWFsaXplID0gc2VyaWFsaXplcnNba10/LnNlcmlhbGl6ZTtcblx0XHRcdFx0XHRpZiAoc2VyaWFsaXplKSB7XG5cdFx0XHRcdFx0XHRzdGF0ZVtrXSA9IHNlcmlhbGl6ZShzdGF0ZVtrXSwgdGhpcyk7XG5cdFx0XHRcdFx0fSBlbHNlIGlmIChrID09PSBcImxheW91dFwiIHx8IGsgPT09IFwic3R5bGVcIikge1xuXHRcdFx0XHRcdFx0Ly8gVGhlc2Uga2V5cyBjb21lIGZyb20gaXB5d2lkZ2V0cywgcmVseSBvbiBKU09OLnN0cmluZ2lmeSB0cmljay5cblx0XHRcdFx0XHRcdHN0YXRlW2tdID0gSlNPTi5wYXJzZShKU09OLnN0cmluZ2lmeShzdGF0ZVtrXSkpO1xuXHRcdFx0XHRcdH0gZWxzZSB7XG5cdFx0XHRcdFx0XHRzdGF0ZVtrXSA9IHN0cnVjdHVyZWRDbG9uZShzdGF0ZVtrXSk7XG5cdFx0XHRcdFx0fVxuXHRcdFx0XHRcdGlmICh0eXBlb2Ygc3RhdGVba10/LnRvSlNPTiA9PT0gXCJmdW5jdGlvblwiKSB7XG5cdFx0XHRcdFx0XHRzdGF0ZVtrXSA9IHN0YXRlW2tdLnRvSlNPTigpO1xuXHRcdFx0XHRcdH1cblx0XHRcdFx0fSBjYXRjaCAoZSkge1xuXHRcdFx0XHRcdGNvbnNvbGUuZXJyb3IoXCJFcnJvciBzZXJpYWxpemluZyB3aWRnZXQgc3RhdGUgYXR0cmlidXRlOiBcIiwgayk7XG5cdFx0XHRcdFx0dGhyb3cgZTtcblx0XHRcdFx0fVxuXHRcdFx0fVxuXHRcdFx0cmV0dXJuIHN0YXRlO1xuXHRcdH1cblx0fVxuXG5cdGNsYXNzIEFueVZpZXcgZXh0ZW5kcyBET01XaWRnZXRWaWV3IHtcblx0XHQjY29udHJvbGxlciA9IG5ldyBBYm9ydENvbnRyb2xsZXIoKTtcblx0XHRhc3luYyByZW5kZXIoKSB7XG5cdFx0XHRsZXQgcnVudGltZSA9IFJVTlRJTUVTLmdldCh0aGlzLm1vZGVsKTtcblx0XHRcdGFzc2VydChydW50aW1lLCBcIlthbnl3aWRnZXRdIFJ1bnRpbWUgbm90IGZvdW5kLlwiKTtcblx0XHRcdGF3YWl0IHJ1bnRpbWUuY3JlYXRlX3ZpZXcodGhpcywgeyBzaWduYWw6IHRoaXMuI2NvbnRyb2xsZXIuc2lnbmFsIH0pO1xuXHRcdH1cblx0XHRyZW1vdmUoKSB7XG5cdFx0XHR0aGlzLiNjb250cm9sbGVyLmFib3J0KFwiW2FueXdpZGdldF0gVmlldyBkZXN0cm95ZWQuXCIpO1xuXHRcdFx0c3VwZXIucmVtb3ZlKCk7XG5cdFx0fVxuXHR9XG5cblx0cmV0dXJuIHsgQW55TW9kZWwsIEFueVZpZXcgfTtcbn1cbiIsImltcG9ydCBjcmVhdGUgZnJvbSBcIi4vd2lkZ2V0LmpzXCI7XG5cbi8vIEB0cy1leHBlY3QtZXJyb3IgLS0gZGVmaW5lIGlzIGEgZ2xvYmFsIHByb3ZpZGVkIGJ5IHRoZSBub3RlYm9vayBydW50aW1lLlxuZGVmaW5lKFtcIkBqdXB5dGVyLXdpZGdldHMvYmFzZVwiXSwgY3JlYXRlKTtcbiIsIl9fd2VicGFja19yZXF1aXJlX18ubyA9IChvYmosIHByb3ApID0+IChPYmplY3QucHJvdG90eXBlLmhhc093blByb3BlcnR5LmNhbGwob2JqLCBwcm9wKSkiLCJfX3dlYnBhY2tfcmVxdWlyZV9fLnJ2ID0gKCkgPT4gKFwiMS41LjhcIikiLCJcbl9fd2VicGFja19yZXF1aXJlX18uUyA9IHt9O1xuX193ZWJwYWNrX3JlcXVpcmVfXy5pbml0aWFsaXplU2hhcmluZ0RhdGEgPSB7IHNjb3BlVG9TaGFyaW5nRGF0YU1hcHBpbmc6IHsgIH0sIHVuaXF1ZU5hbWU6IFwiQGFueXdpZGdldC9tb25vcmVwb1wiIH07XG52YXIgaW5pdFByb21pc2VzID0ge307XG52YXIgaW5pdFRva2VucyA9IHt9O1xuX193ZWJwYWNrX3JlcXVpcmVfXy5JID0gZnVuY3Rpb24obmFtZSwgaW5pdFNjb3BlKSB7XG5cdGlmICghaW5pdFNjb3BlKSBpbml0U2NvcGUgPSBbXTtcblx0Ly8gaGFuZGxpbmcgY2lyY3VsYXIgaW5pdCBjYWxsc1xuXHR2YXIgaW5pdFRva2VuID0gaW5pdFRva2Vuc1tuYW1lXTtcblx0aWYgKCFpbml0VG9rZW4pIGluaXRUb2tlbiA9IGluaXRUb2tlbnNbbmFtZV0gPSB7fTtcblx0aWYgKGluaXRTY29wZS5pbmRleE9mKGluaXRUb2tlbikgPj0gMCkgcmV0dXJuO1xuXHRpbml0U2NvcGUucHVzaChpbml0VG9rZW4pO1xuXHQvLyBvbmx5IHJ1bnMgb25jZVxuXHRpZiAoaW5pdFByb21pc2VzW25hbWVdKSByZXR1cm4gaW5pdFByb21pc2VzW25hbWVdO1xuXHQvLyBjcmVhdGVzIGEgbmV3IHNoYXJlIHNjb3BlIGlmIG5lZWRlZFxuXHRpZiAoIV9fd2VicGFja19yZXF1aXJlX18ubyhfX3dlYnBhY2tfcmVxdWlyZV9fLlMsIG5hbWUpKVxuXHRcdF9fd2VicGFja19yZXF1aXJlX18uU1tuYW1lXSA9IHt9O1xuXHQvLyBydW5zIGFsbCBpbml0IHNuaXBwZXRzIGZyb20gYWxsIG1vZHVsZXMgcmVhY2hhYmxlXG5cdHZhciBzY29wZSA9IF9fd2VicGFja19yZXF1aXJlX18uU1tuYW1lXTtcblx0dmFyIHdhcm4gPSBmdW5jdGlvbiAobXNnKSB7XG5cdFx0aWYgKHR5cGVvZiBjb25zb2xlICE9PSBcInVuZGVmaW5lZFwiICYmIGNvbnNvbGUud2FybikgY29uc29sZS53YXJuKG1zZyk7XG5cdH07XG5cdHZhciB1bmlxdWVOYW1lID0gX193ZWJwYWNrX3JlcXVpcmVfXy5pbml0aWFsaXplU2hhcmluZ0RhdGEudW5pcXVlTmFtZTtcblx0dmFyIHJlZ2lzdGVyID0gZnVuY3Rpb24gKG5hbWUsIHZlcnNpb24sIGZhY3RvcnksIGVhZ2VyKSB7XG5cdFx0dmFyIHZlcnNpb25zID0gKHNjb3BlW25hbWVdID0gc2NvcGVbbmFtZV0gfHwge30pO1xuXHRcdHZhciBhY3RpdmVWZXJzaW9uID0gdmVyc2lvbnNbdmVyc2lvbl07XG5cdFx0aWYgKFxuXHRcdFx0IWFjdGl2ZVZlcnNpb24gfHxcblx0XHRcdCghYWN0aXZlVmVyc2lvbi5sb2FkZWQgJiZcblx0XHRcdFx0KCFlYWdlciAhPSAhYWN0aXZlVmVyc2lvbi5lYWdlclxuXHRcdFx0XHRcdD8gZWFnZXJcblx0XHRcdFx0XHQ6IHVuaXF1ZU5hbWUgPiBhY3RpdmVWZXJzaW9uLmZyb20pKVxuXHRcdClcblx0XHRcdHZlcnNpb25zW3ZlcnNpb25dID0geyBnZXQ6IGZhY3RvcnksIGZyb206IHVuaXF1ZU5hbWUsIGVhZ2VyOiAhIWVhZ2VyIH07XG5cdH07XG5cdHZhciBpbml0RXh0ZXJuYWwgPSBmdW5jdGlvbiAoaWQpIHtcblx0XHR2YXIgaGFuZGxlRXJyb3IgPSBmdW5jdGlvbiAoZXJyKSB7XG5cdFx0XHR3YXJuKFwiSW5pdGlhbGl6YXRpb24gb2Ygc2hhcmluZyBleHRlcm5hbCBmYWlsZWQ6IFwiICsgZXJyKTtcblx0XHR9O1xuXHRcdHRyeSB7XG5cdFx0XHR2YXIgbW9kdWxlID0gX193ZWJwYWNrX3JlcXVpcmVfXyhpZCk7XG5cdFx0XHRpZiAoIW1vZHVsZSkgcmV0dXJuO1xuXHRcdFx0dmFyIGluaXRGbiA9IGZ1bmN0aW9uIChtb2R1bGUpIHtcblx0XHRcdFx0cmV0dXJuIChcblx0XHRcdFx0XHRtb2R1bGUgJiZcblx0XHRcdFx0XHRtb2R1bGUuaW5pdCAmJlxuXHRcdFx0XHRcdG1vZHVsZS5pbml0KF9fd2VicGFja19yZXF1aXJlX18uU1tuYW1lXSwgaW5pdFNjb3BlKVxuXHRcdFx0XHQpO1xuXHRcdFx0fTtcblx0XHRcdGlmIChtb2R1bGUudGhlbikgcmV0dXJuIHByb21pc2VzLnB1c2gobW9kdWxlLnRoZW4oaW5pdEZuLCBoYW5kbGVFcnJvcikpO1xuXHRcdFx0dmFyIGluaXRSZXN1bHQgPSBpbml0Rm4obW9kdWxlKTtcblx0XHRcdGlmIChpbml0UmVzdWx0ICYmIGluaXRSZXN1bHQudGhlbilcblx0XHRcdFx0cmV0dXJuIHByb21pc2VzLnB1c2goaW5pdFJlc3VsdFtcImNhdGNoXCJdKGhhbmRsZUVycm9yKSk7XG5cdFx0fSBjYXRjaCAoZXJyKSB7XG5cdFx0XHRoYW5kbGVFcnJvcihlcnIpO1xuXHRcdH1cblx0fTtcblx0dmFyIHByb21pc2VzID0gW107XG5cdHZhciBzY29wZVRvU2hhcmluZ0RhdGFNYXBwaW5nID0gX193ZWJwYWNrX3JlcXVpcmVfXy5pbml0aWFsaXplU2hhcmluZ0RhdGEuc2NvcGVUb1NoYXJpbmdEYXRhTWFwcGluZztcblx0aWYgKHNjb3BlVG9TaGFyaW5nRGF0YU1hcHBpbmdbbmFtZV0pIHtcblx0XHRzY29wZVRvU2hhcmluZ0RhdGFNYXBwaW5nW25hbWVdLmZvckVhY2goZnVuY3Rpb24gKHN0YWdlKSB7XG5cdFx0XHRpZiAodHlwZW9mIHN0YWdlID09PSBcIm9iamVjdFwiKSByZWdpc3RlcihzdGFnZS5uYW1lLCBzdGFnZS52ZXJzaW9uLCBzdGFnZS5mYWN0b3J5LCBzdGFnZS5lYWdlcik7XG5cdFx0XHRlbHNlIGluaXRFeHRlcm5hbChzdGFnZSlcblx0XHR9KTtcblx0fVxuXHRpZiAoIXByb21pc2VzLmxlbmd0aCkgcmV0dXJuIChpbml0UHJvbWlzZXNbbmFtZV0gPSAxKTtcblx0cmV0dXJuIChpbml0UHJvbWlzZXNbbmFtZV0gPSBQcm9taXNlLmFsbChwcm9taXNlcykudGhlbihmdW5jdGlvbiAoKSB7XG5cdFx0cmV0dXJuIChpbml0UHJvbWlzZXNbbmFtZV0gPSAxKTtcblx0fSkpO1xufTtcblxuIiwiX193ZWJwYWNrX3JlcXVpcmVfXy5ydWlkID0gXCJidW5kbGVyPXJzcGFja0AxLjUuOFwiO1xuIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiI7Ozs7OztBQUFBO0FBQ0E7O0FBRU87QUFDUDs7QUFFQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOztBQUVBLFFBQVEsUUFBUTtBQUNoQjtBQUNBO0FBQ0E7QUFDQTs7QUFFQTtBQUNBOztBQUVBO0FBQ0E7QUFDQTs7O0FDdkJxQztBQUNIOztBQUVsQztBQUNBLGNBQWMsK0JBQStCOztBQUU3QztBQUNBO0FBQ0EsYUFBYSxvQkFBb0I7QUFDakM7O0FBRUE7QUFDQTtBQUNBLHFCQUFxQjtBQUNyQixpQkFBaUI7QUFDakI7O0FBRUE7QUFDQTtBQUNBLGtCQUFrQjtBQUNsQixtQkFBbUI7QUFDbkI7O0FBRUE7QUFDQSxXQUFXLFNBQVM7QUFDcEIsV0FBVyxRQUFRO0FBQ25CLGFBQWE7QUFDYjtBQUNBO0FBQ0E7QUFDQTs7QUFFQTtBQUNBLFdBQVcsUUFBUTtBQUNuQixhQUFhLGtCQUFrQixPQUFPLGNBQWMsT0FBTztBQUMzRDtBQUNBO0FBQ0E7QUFDQTs7QUFFQTtBQUNBLFdBQVcsUUFBUTtBQUNuQixXQUFXLFFBQVE7QUFDbkIsYUFBYTtBQUNiO0FBQ0E7QUFDQSxZQUFZLHdCQUF3QjtBQUNwQywrQ0FBK0MsYUFBYTs7QUFFNUQ7QUFDQTtBQUNBO0FBQ0E7QUFDQSwyQkFBMkIsaUJBQWlCO0FBQzVDO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QUFFQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0EsR0FBRztBQUNIO0FBQ0EsRUFBRTtBQUNGOztBQUVBO0FBQ0EsV0FBVyxRQUFRO0FBQ25CLFdBQVcsUUFBUTtBQUNuQixhQUFhO0FBQ2I7QUFDQTtBQUNBLFlBQVkseUJBQXlCO0FBQ3JDLGdEQUFnRCxhQUFhO0FBQzdEO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFD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