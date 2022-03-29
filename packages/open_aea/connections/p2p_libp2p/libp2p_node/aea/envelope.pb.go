// Code generated by protoc-gen-go. DO NOT EDIT.
// versions:
// 	protoc-gen-go v1.25.0
// 	protoc        (unknown)
// source: envelope.proto

package aea

import (
	"github.com/golang/protobuf/proto"
	"google.golang.org/protobuf/reflect/protoreflect"
	"google.golang.org/protobuf/runtime/protoimpl"
	"reflect"
	"sync"
)

const (
	// Verify that this generated code is sufficiently up-to-date.
	_ = protoimpl.EnforceVersion(20 - protoimpl.MinVersion)
	// Verify that runtime/protoimpl is sufficiently up-to-date.
	_ = protoimpl.EnforceVersion(protoimpl.MaxVersion - 20)
)

// This is a compile-time assertion that a sufficiently up-to-date version
// of the legacy proto package is being used.
const _ = proto.ProtoPackageIsVersion4

type Envelope struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	To         string `protobuf:"bytes,1,opt,name=to,proto3" json:"to,omitempty"`
	Sender     string `protobuf:"bytes,2,opt,name=sender,proto3" json:"sender,omitempty"`
	ProtocolId string `protobuf:"bytes,3,opt,name=protocol_id,json=protocolId,proto3" json:"protocol_id,omitempty"`
	Message    []byte `protobuf:"bytes,4,opt,name=message,proto3" json:"message,omitempty"`
	Uri        string `protobuf:"bytes,5,opt,name=uri,proto3" json:"uri,omitempty"`
}

func (x *Envelope) Reset() {
	*x = Envelope{}
	if protoimpl.UnsafeEnabled {
		mi := &file_envelope_proto_msgTypes[0]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *Envelope) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*Envelope) ProtoMessage() {}

func (x *Envelope) ProtoReflect() protoreflect.Message {
	mi := &file_envelope_proto_msgTypes[0]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use Envelope.ProtoReflect.Descriptor instead.
func (*Envelope) Descriptor() ([]byte, []int) {
	return file_envelope_proto_rawDescGZIP(), []int{0}
}

func (x *Envelope) GetTo() string {
	if x != nil {
		return x.To
	}
	return ""
}

func (x *Envelope) GetSender() string {
	if x != nil {
		return x.Sender
	}
	return ""
}

func (x *Envelope) GetProtocolId() string {
	if x != nil {
		return x.ProtocolId
	}
	return ""
}

func (x *Envelope) GetMessage() []byte {
	if x != nil {
		return x.Message
	}
	return nil
}

func (x *Envelope) GetUri() string {
	if x != nil {
		return x.Uri
	}
	return ""
}

var File_envelope_proto protoreflect.FileDescriptor

var file_envelope_proto_rawDesc = []byte{
	0x0a, 0x0e, 0x65, 0x6e, 0x76, 0x65, 0x6c, 0x6f, 0x70, 0x65, 0x2e, 0x70, 0x72, 0x6f, 0x74, 0x6f,
	0x12, 0x03, 0x61, 0x65, 0x61, 0x22, 0x7f, 0x0a, 0x08, 0x45, 0x6e, 0x76, 0x65, 0x6c, 0x6f, 0x70,
	0x65, 0x12, 0x0e, 0x0a, 0x02, 0x74, 0x6f, 0x18, 0x01, 0x20, 0x01, 0x28, 0x09, 0x52, 0x02, 0x74,
	0x6f, 0x12, 0x16, 0x0a, 0x06, 0x73, 0x65, 0x6e, 0x64, 0x65, 0x72, 0x18, 0x02, 0x20, 0x01, 0x28,
	0x09, 0x52, 0x06, 0x73, 0x65, 0x6e, 0x64, 0x65, 0x72, 0x12, 0x1f, 0x0a, 0x0b, 0x70, 0x72, 0x6f,
	0x74, 0x6f, 0x63, 0x6f, 0x6c, 0x5f, 0x69, 0x64, 0x18, 0x03, 0x20, 0x01, 0x28, 0x09, 0x52, 0x0a,
	0x70, 0x72, 0x6f, 0x74, 0x6f, 0x63, 0x6f, 0x6c, 0x49, 0x64, 0x12, 0x18, 0x0a, 0x07, 0x6d, 0x65,
	0x73, 0x73, 0x61, 0x67, 0x65, 0x18, 0x04, 0x20, 0x01, 0x28, 0x0c, 0x52, 0x07, 0x6d, 0x65, 0x73,
	0x73, 0x61, 0x67, 0x65, 0x12, 0x10, 0x0a, 0x03, 0x75, 0x72, 0x69, 0x18, 0x05, 0x20, 0x01, 0x28,
	0x09, 0x52, 0x03, 0x75, 0x72, 0x69, 0x62, 0x06, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x33,
}

var (
	file_envelope_proto_rawDescOnce sync.Once
	file_envelope_proto_rawDescData = file_envelope_proto_rawDesc
)

func file_envelope_proto_rawDescGZIP() []byte {
	file_envelope_proto_rawDescOnce.Do(func() {
		file_envelope_proto_rawDescData = protoimpl.X.CompressGZIP(file_envelope_proto_rawDescData)
	})
	return file_envelope_proto_rawDescData
}

var file_envelope_proto_msgTypes = make([]protoimpl.MessageInfo, 1)
var file_envelope_proto_goTypes = []interface{}{
	(*Envelope)(nil), // 0: aea.Envelope
}
var file_envelope_proto_depIdxs = []int32{
	0, // [0:0] is the sub-list for method output_type
	0, // [0:0] is the sub-list for method input_type
	0, // [0:0] is the sub-list for extension type_name
	0, // [0:0] is the sub-list for extension extendee
	0, // [0:0] is the sub-list for field type_name
}

func init() { file_envelope_proto_init() }
func file_envelope_proto_init() {
	if File_envelope_proto != nil {
		return
	}
	if !protoimpl.UnsafeEnabled {
		file_envelope_proto_msgTypes[0].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*Envelope); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
	}
	type x struct{}
	out := protoimpl.TypeBuilder{
		File: protoimpl.DescBuilder{
			GoPackagePath: reflect.TypeOf(x{}).PkgPath(),
			RawDescriptor: file_envelope_proto_rawDesc,
			NumEnums:      0,
			NumMessages:   1,
			NumExtensions: 0,
			NumServices:   0,
		},
		GoTypes:           file_envelope_proto_goTypes,
		DependencyIndexes: file_envelope_proto_depIdxs,
		MessageInfos:      file_envelope_proto_msgTypes,
	}.Build()
	File_envelope_proto = out.File
	file_envelope_proto_rawDesc = nil
	file_envelope_proto_goTypes = nil
	file_envelope_proto_depIdxs = nil
}
